"""Collecte d'offres sur le web.

- Quand une recherche web est disponible (recherche intégrée du fournisseur, ou service externe
  Brave, Tavily ou SearXNG : voir ``settings.web_search``), le modèle mène la recherche en suivant
  la liste de sources et les consignes de la configuration.
- Sinon, les pages publiques listées dans les sources sont téléchargées et le modèle en extrait
  les offres (couverture plus limitée).
"""

from __future__ import annotations

import logging
from typing import Any

from .. import llm
from ..settings import settings

log = logging.getLogger(__name__)

OFFER_SHAPE = (
    '[{"title": str, "company": str, "location": str, "contract": str, "remote": str, '
    '"salary": str, "url": str, "source": str, "published": "AAAA-MM-JJ ou vide", '
    '"kind": "emploi" ou "associe", "raw_text": "résumé factuel de l\'annonce en 3 phrases"}]'
)


def _criteria(config: dict[str, Any]) -> str:
    keys = ["roles", "domains", "geo", "contracts", "exclusions", "partners", "free"]
    parts = [f"{k.upper()} :\n{config.get(k, '')}" for k in keys if config.get(k)]
    if config.get("salary_min_k"):
        parts.append(f"RÉMUNÉRATION PLANCHER : {config['salary_min_k']} k€ brut annuel")
    return "\n\n".join(parts)


def _sources(config: dict[str, Any]) -> str:
    lines = []
    for s in config.get("sources", []):
        if s.get("active") is False:
            continue
        lines.append(f"- {s.get('name')} {s.get('url', '')} {('— ' + s['note']) if s.get('note') else ''}".strip())
    return "\n".join(lines)


def search(config: dict[str, Any], known_urls: list[str], max_jobs: int = 25, max_partners: int = 5) -> list[dict[str, Any]]:
    from ..settings import web_search_backend

    if web_search_backend(settings) != "none":
        return _search_claude(config, known_urls, max_jobs, max_partners)
    return _search_fetch(config, max_jobs)


def _search_claude(config: dict[str, Any], known_urls: list[str], max_jobs: int, max_partners: int) -> list[dict[str, Any]]:
    prompt = f"""Tu fais la veille emploi d'un candidat. Cherche des offres récentes (publiées depuis environ 7 jours)
correspondant à ses critères, en suivant les consignes données pour chaque source. Cherche aussi, si la configuration
le demande, des porteurs de projet qui recherchent un associé ou un cofondateur (annonces d'environ 30 jours).

CRITÈRES
{_criteria(config)}

SOURCES (consignes entre tirets)
{_sources(config)}

Ne lis jamais LinkedIn directement. N'invente aucune information : un champ inconnu s'écrit « non précisé ».
Ignore les offres déjà connues dont l'url figure ici : {', '.join(known_urls[-300:]) or 'aucune'}.
Rapporte au plus {max_jobs} offres d'emploi et {max_partners} recherches d'associés, au format :
{OFFER_SHAPE}"""
    try:
        data = llm.web_research_json(prompt, tier="default", country=config.get("country") or "FR")
        return data if isinstance(data, list) else []
    except Exception as e:  # noqa: BLE001
        log.warning("Recherche web impossible, repli sur la lecture des sources : %s", e)
        return _search_fetch(config, max_jobs)


def _search_fetch(config: dict[str, Any], max_jobs: int) -> list[dict[str, Any]]:
    import httpx

    from .email_imap import html_to_text

    found: list[dict[str, Any]] = []
    headers = {"User-Agent": "Mozilla/5.0 (huntboard; personal use)"}
    for s in config.get("sources", []):
        url = s.get("url")
        if s.get("active") is False or not url or "linkedin.com" in url:
            continue
        try:
            r = httpx.get(url, headers=headers, timeout=20, follow_redirects=True)
            r.raise_for_status()
        except Exception as e:  # noqa: BLE001
            log.info("Source %s inaccessible : %s", s.get("name"), e)
            continue
        text = html_to_text(r.text)[:30000]
        prompt = (
            f"Extrais de cette page les offres correspondant aux critères ci-dessous (au plus 10).\n\n"
            f"CRITÈRES\n{_criteria(config)}\n\nPAGE ({url})\n{text}\n\nFormat : {OFFER_SHAPE}"
        )
        try:
            items = llm.complete_json(prompt, tier="quick")
            for it in items if isinstance(items, list) else []:
                it.setdefault("source", s.get("name"))
                found.append(it)
        except Exception as e:  # noqa: BLE001
            log.info("Extraction impossible pour %s : %s", s.get("name"), e)
        if len(found) >= max_jobs:
            break
    return found[:max_jobs]
