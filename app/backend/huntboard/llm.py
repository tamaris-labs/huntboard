"""Couche d'accès au modèle de langage, indépendante du fournisseur.

Fournisseurs pris en charge :
- ``anthropic`` : API Claude (recommandé ; seul fournisseur offrant la recherche web intégrée) ;
- ``openai`` : toute API compatible OpenAI (OpenAI, Gemini via son point d'accès compatible,
  Ollama, Mistral, etc.), choisie avec ``LLM_BASE_URL``.

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


def web_research_json(prompt: str, tier: str = "default", country: str = "FR",
                      allowed_domains: list[str] | None = None) -> Any:
    """Recherche web menée par Claude (outil web_search de l'API), réponse finale en JSON.

    Disponible uniquement avec le fournisseur ``anthropic``.
    """
    if settings.llm_provider != "anthropic" or not settings.llm_api_key:
        raise LLMUnavailable("La recherche web intégrée nécessite le fournisseur anthropic.")
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
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": prompt + "\n\nTermine par un unique bloc JSON valide, sans texte après."}
    ]
    for _ in range(4):  # une recherche longue peut être mise en pause par l'API
        resp = client.messages.create(model=_model(tier), max_tokens=8192, tools=[tool], messages=messages)
        if resp.stop_reason != "pause_turn":
            break
        messages = messages + [{"role": "assistant", "content": resp.content}]
    text = "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text")
    return parse_json(text)
