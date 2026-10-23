"""Couche d'accès au modèle de langage, indépendante du fournisseur.

Fournisseurs pris en charge :
- ``anthropic`` : API Claude (recommandé) ;
- ``openai`` : toute API compatible OpenAI (OpenAI, Gemini via son point d'accès compatible,
  Mistral, Grok, OpenRouter, Ollama, etc.), choisie avec ``LLM_BASE_URL``.

Recherche web (``web_research_json``) : recherche intégrée du fournisseur quand elle existe
(Anthropic, OpenAI, Grok, OpenRouter, Gemini), sinon service externe (Brave, Tavily, SearXNG)
interrogé par le modèle comme un outil — ce qui fonctionne aussi avec un modèle local.

Trois niveaux de modèle : ``quick`` (extraction, tri), ``default`` (conversation),
``complex`` (notation fine, préparation d'entretien).
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterator
from typing import Any

from .settings import settings

Messages = list[dict[str, str]]


class LLMUnavailable(RuntimeError):
    """Aucun fournisseur configuré, ou fournisseur injoignable."""


def _model(tier: str) -> str:
    return {"quick": settings.model_quick, "complex": settings.model_complex}.get(tier, settings.model_default)


def _as_messages(prompt: str | Messages) -> Messages:
    if isinstance(prompt, str):
        return [{"role": "user", "content": prompt}]
    return [{"role": m["role"], "content": m["content"]} for m in prompt]


def stream(prompt: str | Messages, tier: str = "default", max_tokens: int = 4096) -> Iterator[str]:
    """Produit la réponse au fil de l'eau, morceau par morceau."""
    if not settings.llm_enabled:
        raise LLMUnavailable("Aucun modèle configuré : renseignez LLM_API_KEY dans le fichier .env.")
    messages = _as_messages(prompt)
    if settings.llm_provider == "anthropic":
        import anthropic

        client = anthropic.Anthropic(api_key=settings.llm_api_key)
        with client.messages.stream(model=_model(tier), max_tokens=max_tokens, messages=messages) as s:
            yield from s.text_stream
    else:
        from openai import OpenAI

        client = OpenAI(api_key=settings.llm_api_key or "none", base_url=settings.llm_base_url or None)
        resp = client.chat.completions.create(model=_model(tier), messages=messages, max_tokens=max_tokens, stream=True)
        for chunk in resp:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta


def complete(prompt: str | Messages, tier: str = "default", max_tokens: int = 4096,
             on_text: Callable[[str], None] | None = None) -> str:
    parts: list[str] = []
    for piece in stream(prompt, tier=tier, max_tokens=max_tokens):
        parts.append(piece)
        if on_text:
            on_text("".join(parts))
    return "".join(parts)


def to_openai_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convertit des messages au format Anthropic (blocs text / tool_use / tool_result) vers le format OpenAI."""
    out: list[dict[str, Any]] = []
    for m in messages:
        content = m.get("content")
        if isinstance(content, str):
            out.append({"role": m["role"], "content": content})
            continue
        texts = [b.get("text", "") for b in content if b.get("type") == "text"]
        if m["role"] == "assistant":
            calls = [{"id": b["id"], "type": "function", "function": {"name": b["name"], "arguments": json.dumps(b.get("input") or {})}}
                     for b in content if b.get("type") == "tool_use"]
            msg: dict[str, Any] = {"role": "assistant", "content": "\n".join(texts) or None}
            if calls:
                msg["tool_calls"] = calls
            out.append(msg)
        else:
            for b in content:
                if b.get("type") == "tool_result":
                    c = b.get("content")
                    out.append({"role": "tool", "tool_call_id": b["tool_use_id"], "content": c if isinstance(c, str) else json.dumps(c)})
            if texts:
                out.append({"role": "user", "content": "\n".join(texts)})
    return out


def tool_step(messages: list[dict[str, Any]], tools: list[dict[str, Any]], tier: str = "default",
              max_tokens: int = 4096) -> dict[str, Any]:
    """Un tour de conversation avec outils : renvoie {content: [blocs text/tool_use], stop_reason}."""
    if not settings.llm_enabled:
        raise LLMUnavailable("Aucun modèle configuré : renseignez LLM_API_KEY dans le fichier .env.")
    if settings.llm_provider == "anthropic":
        import anthropic

        client = anthropic.Anthropic(api_key=settings.llm_api_key)
        r = client.messages.create(model=_model(tier), max_tokens=max_tokens, messages=messages,
                                   tools=[{"name": t["name"], "description": t.get("description", ""),
                                           "input_schema": t.get("input_schema") or {"type": "object", "properties": {}}} for t in tools])
        blocks = []
        for b in r.content:
            if b.type == "text":
                blocks.append({"type": "text", "text": b.text})
            elif b.type == "tool_use":
                blocks.append({"type": "tool_use", "id": b.id, "name": b.name, "input": b.input})
        return {"content": blocks, "stop_reason": r.stop_reason}
    from openai import OpenAI

    client = OpenAI(api_key=settings.llm_api_key or "none", base_url=settings.llm_base_url or None)
    r = client.chat.completions.create(
        model=_model(tier), max_tokens=max_tokens, messages=to_openai_messages(messages),
        tools=[{"type": "function", "function": {"name": t["name"], "description": t.get("description", ""),
                                                  "parameters": t.get("input_schema") or {"type": "object", "properties": {}}}} for t in tools])
    msg = r.choices[0].message
    blocks = [{"type": "text", "text": msg.content}] if msg.content else []
    for c in msg.tool_calls or []:
        try:
            args = json.loads(c.function.arguments or "{}")
        except ValueError:
            args = {}
        blocks.append({"type": "tool_use", "id": c.id, "name": c.function.name, "input": args})
    return {"content": blocks, "stop_reason": "tool_use" if msg.tool_calls else "end_turn"}


def complete_json(prompt: str, tier: str = "quick", max_tokens: int = 8192) -> Any:
    text = complete(prompt + "\n\nRéponds uniquement avec du JSON valide, sans texte autour.", tier=tier, max_tokens=max_tokens)
    return parse_json(text)


def parse_json(text: str) -> Any:
    """Lecture tolérante : JSON brut, bloc ```json```, ou premier objet/tableau trouvé."""
    text = text.strip()
    try:
        return json.loads(text)
    except ValueError:
        pass
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        try:
            return json.loads(fence.group(1))
        except ValueError:
            pass
    starts = [i for i in (text.find("["), text.find("{")) if i >= 0]
    if starts:
        start = min(starts)
        end = max(text.rfind("]"), text.rfind("}"))
        if end > start:
            return json.loads(text[start : end + 1])
    raise ValueError("Réponse sans JSON exploitable")


JSON_TAIL = "\n\nTermine par un unique bloc JSON valide, sans texte après."


def web_research_json(prompt: str, tier: str = "default", country: str = "FR",
                      allowed_domains: list[str] | None = None) -> Any:
    """Recherche web menée par le modèle, réponse finale en JSON.

    Le moyen dépend de ``settings.web_search`` et du fournisseur (voir ``web_search_backend``) ;
    lève ``LLMUnavailable`` quand aucune recherche web n'est disponible.
    """
    from .settings import web_search_backend

    backend = web_search_backend(settings)
    if backend == "none":
        raise LLMUnavailable("Aucune recherche web configurée.")
    if backend == "native:anthropic":
        text = _research_anthropic(prompt, tier, country, allowed_domains)
    elif backend in ("native:openai", "native:xai"):
        text = _research_responses(prompt, tier)
    elif backend == "native:openrouter":
        text = _research_openrouter(prompt, tier)
    elif backend == "native:gemini":
        text = _research_gemini(prompt, tier)
    else:
        text = _research_with_tools(prompt, tier, backend, country)
    return parse_json(text)


def _research_anthropic(prompt: str, tier: str, country: str, allowed_domains: list[str] | None) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.llm_api_key)
    tool: dict[str, Any] = {
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": settings.web_search_max_uses,
        "user_location": {"type": "approximate", "country": country, "timezone": settings.timezone},
    }
    if allowed_domains:
        tool["allowed_domains"] = allowed_domains
    messages: list[dict[str, Any]] = [{"role": "user", "content": prompt + JSON_TAIL}]
    for _ in range(4):  # une recherche longue peut être mise en pause par l'API
        resp = client.messages.create(model=_model(tier), max_tokens=8192, tools=[tool], messages=messages)
        if resp.stop_reason != "pause_turn":
            break
        messages = messages + [{"role": "assistant", "content": resp.content}]
    return "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text")


def _http():
    import httpx

    return httpx.Client(timeout=180)


def _base(default: str) -> str:
    return (settings.llm_base_url or default).rstrip("/")


def _research_responses(prompt: str, tier: str) -> str:
    """OpenAI et Grok (xAI) : API Responses avec l'outil web_search."""
    url = _base("https://api.openai.com/v1") + "/responses"
    body = {"model": _model(tier), "input": prompt + JSON_TAIL, "tools": [{"type": "web_search"}]}
    with _http() as c:
        r = c.post(url, json=body, headers={"Authorization": f"Bearer {settings.llm_api_key}"})
        r.raise_for_status()
        data = r.json()
    if data.get("output_text"):
        return data["output_text"]
    return "".join(part.get("text", "") for item in data.get("output") or [] if item.get("type") == "message"
                   for part in item.get("content") or [] if part.get("type") in ("output_text", "text"))


def _research_openrouter(prompt: str, tier: str) -> str:
    """OpenRouter : suffixe « :online » sur le modèle (recherche web pour tout modèle)."""
    from openai import OpenAI

    model = _model(tier)
    model = model if model.endswith(":online") else model + ":online"
    client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
    r = client.chat.completions.create(model=model, max_tokens=8192, messages=[{"role": "user", "content": prompt + JSON_TAIL}])
    return r.choices[0].message.content or ""


def _research_gemini(prompt: str, tier: str) -> str:
    """Gemini : API native generateContent avec l'ancrage Google Search."""
    model = _model(tier).removeprefix("models/")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {"contents": [{"role": "user", "parts": [{"text": prompt + JSON_TAIL}]}], "tools": [{"google_search": {}}]}
    with _http() as c:
        r = c.post(url, json=body, headers={"x-goog-api-key": settings.llm_api_key})
        r.raise_for_status()
        data = r.json()
    parts = ((data.get("candidates") or [{}])[0].get("content") or {}).get("parts") or []
    return "".join(p.get("text", "") for p in parts)


# Service de recherche externe, interrogé par le modèle comme un outil ---------------
def search_web(query: str, backend: str, country: str = "FR", count: int = 8) -> list[dict[str, str]]:
    """Résultats [{title, url, snippet}] de Brave, Tavily ou SearXNG."""
    with _http() as c:
        if backend == "brave":
            r = c.get("https://api.search.brave.com/res/v1/web/search", params={"q": query, "count": count, "country": country.lower()},
                      headers={"X-Subscription-Token": settings.search_api_key, "Accept": "application/json"})
            r.raise_for_status()
            items = (r.json().get("web") or {}).get("results") or []
            return [{"title": i.get("title", ""), "url": i.get("url", ""), "snippet": i.get("description", "")} for i in items[:count]]
        if backend == "tavily":
            r = c.post("https://api.tavily.com/search", json={"query": query, "max_results": count},
                       headers={"Authorization": f"Bearer {settings.search_api_key}"})
            r.raise_for_status()
            return [{"title": i.get("title", ""), "url": i.get("url", ""), "snippet": i.get("content", "")} for i in (r.json().get("results") or [])[:count]]
        if backend == "searxng":
            r = c.get(settings.searxng_url.rstrip("/") + "/search", params={"q": query, "format": "json"})
            r.raise_for_status()
            return [{"title": i.get("title", ""), "url": i.get("url", ""), "snippet": i.get("content", "")} for i in (r.json().get("results") or [])[:count]]
    raise LLMUnavailable(f"Service de recherche inconnu : {backend}")


def read_page(url: str, limit: int = 12000) -> str:
    import httpx

    from .sources.email_imap import html_to_text

    if "linkedin.com" in url:
        return "Page non lue : LinkedIn n'est jamais lu directement."
    r = httpx.get(url, timeout=20, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (Huntboard; personal job search)"})
    r.raise_for_status()
    return " ".join(html_to_text(r.text).split())[:limit]


RESEARCH_TOOLS = [
    {"name": "web_search", "description": "Search the web. Returns titles, URLs and snippets.",
     "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "read_page", "description": "Read the text of a public web page.",
     "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}},
]


def _research_with_tools(prompt: str, tier: str, backend: str, country: str, step=None, search=None, read=None) -> str:
    """Boucle outil : le modèle (quel qu'il soit, local compris) cherche et lit des pages, puis répond."""
    step = step or tool_step
    search = search or (lambda q: search_web(q, backend, country))
    read = read or read_page
    messages: list[dict[str, Any]] = [{"role": "user", "content": prompt + "\n\nUse the web_search and read_page tools as needed." + JSON_TAIL}]
    budget = max(4, settings.web_search_max_uses)
    for _ in range(budget):
        r = step(messages, RESEARCH_TOOLS, tier=tier, max_tokens=8192)
        calls = [b for b in r["content"] if b.get("type") == "tool_use"]
        if not calls:
            return "".join(b.get("text", "") for b in r["content"] if b.get("type") == "text")
        messages.append({"role": "assistant", "content": r["content"]})
        results = []
        for b in calls:
            try:
                out: Any = search(str(b["input"].get("query", ""))) if b["name"] == "web_search" else read(str(b["input"].get("url", "")))
            except Exception as e:  # noqa: BLE001
                out = f"Erreur : {e}"
            results.append({"type": "tool_result", "tool_use_id": b["id"], "content": out if isinstance(out, str) else json.dumps(out, ensure_ascii=False)})
        messages.append({"role": "user", "content": results})
    messages.append({"role": "user", "content": "Stop searching now and give the final answer." + JSON_TAIL})
    r = step(messages, RESEARCH_TOOLS, tier=tier, max_tokens=8192)
    return "".join(b.get("text", "") for b in r["content"] if b.get("type") == "text")
