"""Passage de veille : apprentissage, alertes e-mail, recherche web, notation, écriture.

Équivalent autonome de la tâche programmée du kit Claude.
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from . import llm
from .settings import settings
from .sources import email_imap, web
from .store import Store, now_iso

log = logging.getLogger(__name__)

POSITIVE = {"creuser", "postule", "entretien", "offre"}


def slug(*parts: str) -> str:
    s = "-".join(p for p in parts if p)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:80] or "offre"


def dedupe_key(o: dict[str, Any]) -> str:
    m = re.search(r"jobs/view/(\d+)", o.get("url", ""))
    if m:
        return "li:" + m.group(1)
    return slug(o.get("company", ""), o.get("title", ""))


# 1. Apprentissage -------------------------------------------------------------
def learn(store: Store, offers: dict[str, dict], notes: dict[str, dict]) -> dict[str, Any]:
    current = store.data("config", "learned") or {"lessons": [], "rejected": []}
    signals = []
    for oid, n in notes.items():
        o = offers.get(oid)
        if not o or o.get("track"):
            continue  # les pistes complémentaires n'influencent pas la notation du fil principal
        st = n.get("status", "nouvelle")
        if st == "ecartee":
            kind = "écartée"
        elif n.get("fav") or st in POSITIVE:
            kind = "retenue"
        else:
            continue  # « non_retenu » = refus du recruteur : pas un signal de préférence
        signals.append({
            "signal": kind, "motifs": n.get("neg_tags" if kind == "écartée" else "pos_tags", []),
            "note": (n.get("note") or "")[:300], "title": o.get("title"), "company": o.get("company"),
            "location": o.get("location"), "remote": o.get("remote"), "salary": o.get("salary"),
            "source": o.get("source"), "score": o.get("score"),
        })
    if len(signals) < 2 or not settings.llm_enabled:
        return current
    prompt = f"""Voici les choix d'un candidat sur des offres d'emploi (offres écartées ou retenues, avec motifs).
Dégage au plus 8 tendances, chacune appuyée sur au moins deux signaux concordants, en une phrase factuelle,
avec un effet chiffré sur la notation (plafonné à ±10 points) et la preuve.
N'utilise jamais une tendance figurant dans cette liste rejetée par le candidat : {json.dumps(current.get('rejected', []), ensure_ascii=False)}
N'invente pas de tendance faute de signaux suffisants (liste vide acceptée).
Rédige les tendances {"en anglais" if (store.data("config", "main") or {}).get("lang") == "en" else "en français"}.

SIGNAUX
{json.dumps(signals, ensure_ascii=False)[:40000]}

Format : [{{"text": str, "effect": str, "evidence": str}}]"""
    try:
        lessons = llm.complete_json(prompt, tier="default")
        if isinstance(lessons, list):
            current = {**current, "lessons": lessons[:8], "updated_at": now_iso()}
            store.set("config", "learned", current)
    except Exception as e:  # noqa: BLE001
        log.warning("Apprentissage impossible : %s", e)
    return current


# 2. Alertes e-mail ------------------------------------------------------------
def offers_from_mail(days: int) -> tuple[list[dict[str, Any]], list[str]]:
    """Renvoie (offres candidates, événements notables : expirations, candidatures)."""
    mails = email_imap.fetch_alerts(days=days)
    candidates: list[dict[str, Any]] = []
    events: list[str] = []
    others: list[str] = []
    for m in mails:
        if re.search(r"expire le|candidature a été envoyée|candidature est arrivée", m.subject, re.I):
            events.append(f"{m.date[:10]} — {m.subject}")
        if "linkedin.com" in m.sender:
            for item in email_imap.parse_linkedin_alert(m.text):
                candidates.append({"url": item["url"], "source": "Alerte LinkedIn", "raw_text": item["title_block"]})
        else:
            others.append(f"### {m.subject} ({m.sender})\n{m.text[:6000]}")
    # Mise en forme des blocs LinkedIn et extraction des autres alertes par le modèle
    if candidates or others:
        prompt = (
            "Mets en forme ces offres issues d'alertes e-mail. Pour chaque bloc LinkedIn, sépare intitulé, entreprise "
            "et lieu. Pour les autres e-mails, extrais chaque offre avec son lien direct. Champs inconnus : « non précisé ».\n\n"
            f"BLOCS LINKEDIN\n{json.dumps(candidates, ensure_ascii=False)[:30000]}\n\nAUTRES ALERTES\n" + "\n\n".join(others)[:40000]
            + '\n\nFormat : [{"title","company","location","salary","url","source","raw_text"}]'
        )
        try:
            data = llm.complete_json(prompt, tier="quick")
            candidates = data if isinstance(data, list) else candidates
        except Exception as e:  # noqa: BLE001
            log.warning("Extraction des alertes impossible : %s", e)
    return candidates, events


def follow_up_events(mails: list[Any], offers: dict[str, dict], notes: dict[str, dict],
                     senders_to_skip: list[str]) -> dict[str, list[dict[str, str]]]:
    """Associe les e-mails récents aux candidatures suivies (adresse d'un contact, domaine ou nom de
    l'entreprise dans l'expéditeur ou l'objet). Renvoie {offer_id: [événements nouveaux]}."""
    out: dict[str, list[dict[str, str]]] = {}
    skip = [s.lower() for s in senders_to_skip]
    for oid, n in notes.items():
        if n.get("status") not in POSITIVE:
            continue
        o = offers.get(oid) or {}
        company = (o.get("company") or "").strip().lower()
        keys = {c.get("email", "").strip().lower() for c in n.get("contacts", []) if c.get("email")}
        domains = {k.split("@", 1)[1] for k in keys if "@" in k and not k.endswith(("gmail.com", "outlook.com", "hotmail.com", "yahoo.fr", "yahoo.com"))}
        known = {e.get("text", "") for e in n.get("events", [])}
        for m in mails:
            sender, subject = (m.sender or "").lower(), (m.subject or "")
            if any(s in sender for s in skip):
                continue
            hit = any(k in sender for k in keys) or any(d in sender for d in domains) or (
                len(company) >= 4 and (company in sender or company in subject.lower()))
            if not hit:
                continue
            who = re.sub(r"\s*<.*>", "", m.sender or "").strip() or m.sender
            text = f"E-mail reçu de {who} : {subject}"[:300]
            if text in known:
                continue
            known.add(text)
            out.setdefault(oid, []).append({"at": m.date or now_iso(), "text": text})
    return out


# 2 bis. Accusés de réception de candidature (tout expéditeur) -------------------
ACK_HINT = re.compile(r"candidature|application|applying|postul|accusé de réception", re.I)
ACK_RE = re.compile(
    r"candidature (a été |a bien été |est bien |est |bien )?(envoyée|arrivée|reçue|transmise|enregistrée|prise en compte)"
    r"|accusé de réception|merci (pour|de) votre candidature|confirmation de (votre )?candidature"
    r"|thank(s| you) for (applying|your application)|application (received|submitted|confirmation|has been (received|submitted))"
    r"|(we('ve| have)|has been) received your application|your application (to|for|at|has been)",
    re.I,
)
NOT_ACK_RE = re.compile(r"malheureusement|unfortunately|suite (donnée )?à votre candidature|regret|entretien|interview|update on|mise à jour", re.I)
_NUM = {"deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "two": 2, "three": 3, "four": 4, "five": 5}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def _who(m: Any) -> str:
    return re.sub(r"\s*<.*>", "", m.sender or "").strip() or (m.sender or "")


def ack_header(sender: str, subject: str) -> bool:
    """Premier filtre sur l'en-tête : objet qui évoque une candidature, hors refus et convocations."""
    subject = subject or ""
    return bool(ACK_HINT.search(subject) or ACK_RE.search(subject)) and not NOT_ACK_RE.search(subject)


def is_ack(m: Any) -> bool:
    return ack_header(m.sender, m.subject) and bool(ACK_RE.search(f"{m.subject} {(m.text or '')[:2000]}"))


def response_weeks(text: str) -> int | None:
    """Délai de réponse annoncé (« sans réponse sous 3 semaines… »), en semaines."""
    m = re.search(r"\b(\d{1,2}|deux|trois|quatre|cinq|six|two|three|four|five)\s+(semaines|weeks)\b", text or "", re.I)
    if not m:
        return None
    v = m.group(1).lower()
    return int(v) if v.isdigit() else _NUM.get(v)


def match_offer(m: Any, offers: dict[str, dict]) -> str | None:
    """Offre visée par un accusé : nom de l'entreprise dans l'expéditeur, l'objet ou le début du message ;
    entre plusieurs offres de la même entreprise, celle dont l'intitulé ressort le plus."""
    text = f" {_norm(m.sender)} {_norm(m.subject)} {_norm((m.text or '')[:3000])} "
    best, best_score = None, -1
    for oid, o in offers.items():
        co = _norm(o.get("company") or "")
        if len(co) < 3 or f" {co} " not in text:
            continue
        words = [w for w in _norm(o.get("title") or "").split() if len(w) >= 4]
        sc = sum(1 for w in words if f" {w} " in text)
        if sc > best_score:
            best, best_score = oid, sc
    return best


def ack_details(m: Any) -> dict[str, Any]:
    """Entreprise, intitulé, lieu, référence et portail de suivi d'une candidature, tirés de l'accusé."""
    out: dict[str, Any] = {}
    if settings.llm_enabled:
        prompt = (
            "Cet e-mail confirme une candidature. Extrais l'entreprise qui recrute (pas le site d'annonces ni le "
            "logiciel de recrutement), l'intitulé exact du poste, le lieu, la référence de l'offre et le lien du "
            "portail de suivi ou de l'annonce. Champ inconnu : chaîne vide.\n\n"
            f"EXPÉDITEUR : {m.sender}\nOBJET : {m.subject}\n\n{(m.text or '')[:6000]}\n\n"
            'Format : {"company": str, "title": str, "location": str, "reference": str, "url": str}'
        )
        try:
            data = llm.complete_json(prompt, tier="quick")
            if isinstance(data, dict):
                out = {k: str(v).strip() for k, v in data.items() if v}
        except Exception as e:  # noqa: BLE001
            log.warning("Lecture de l'accusé impossible : %s", e)
    if not out.get("company"):
        g = re.search(r"\b(?:chez|at|to)\s+([A-Z][\w&' .-]{1,40}?)(?:\s*[!.,:-]|$)", m.subject or "")
        if g:
            out["company"] = g.group(1).strip()
    return out


def application_acks(acks: list[Any], offers: dict[str, dict], notes: dict[str, dict],
                     details=ack_details, today: str | None = None) -> dict[str, Any]:
    """Traite les accusés de réception : note « postule » pour une offre connue sans note, simple événement
    si une note existe (statut inchangé), création de l'offre (tier « pending ») si elle est inconnue.
    Plusieurs accusés d'une même candidature (job board et logiciel de l'employeur) ne comptent qu'une fois.
    Renvoie {"offers": {id: offre créée}, "notes": {id: (note complète, nouvelle?)}, "events": [str]}."""
    offers = dict(offers)
    created: dict[str, dict] = {}
    changed: dict[str, tuple[dict, bool]] = {}
    events: list[str] = []
    for m in sorted(acks, key=lambda x: x.date or ""):
        oid = match_offer(m, offers)
        if not oid:
            d = details(m)
            co, title = (d.get("company") or "").strip(), (d.get("title") or "").strip()
            if not co:
                continue
            title = title or (f"Candidature réf. {d['reference']}" if d.get("reference") else "Candidature")
            oid = slug(co, title)
            while oid in offers:
                oid += "-b"
            day = (m.date or today or now_iso())[:10]
            ref = f", référence {d['reference']}" if d.get("reference") else ""
            created[oid] = offers[oid] = {
                "id": oid, "kind": "emploi", "title": title, "company": co,
                "location": d.get("location") or "non précisé", "lat": None, "lon": None,
                "url": d.get("url") or "", "source": "Candidature directe", "tier": "pending", "score": None,
                "raw_text": f"Candidature envoyée le {day} chez {co} pour le poste « {title} »{ref}. "
                            f"Accusé de réception : {m.subject} ({_who(m)}).",
                "found_at": now_iso(),
            }
        who = _who(m)
        weeks = response_weeks(m.text or "")
        text = f"Candidature envoyée (accusé de réception {who})"
        if weeks:
            text += f" ; sans réponse sous {weeks} semaines, à considérer comme non retenue"
        ev = {"at": m.date or now_iso(), "text": text}
        note, is_new = changed.get(oid, (None, False))
        if note is None:
            cur = notes.get(oid)
            note, is_new = (dict(cur), False) if cur else ({}, True)
        if is_new and not note:
            note = {"status": "postule", "applied_at": (m.date or today or now_iso())[:10], "events": []}
        if any(str(e.get("text", "")).startswith("Candidature envoyée") for e in note.get("events") or []):
            continue
        note["events"] = list(note.get("events") or []) + [ev]
        note["updated_at"] = now_iso()
        if weeks and is_new:
            due = datetime.fromisoformat(note["applied_at"]) + timedelta(weeks=weeks)
            note.update({"next_action": "Relancer ou classer si toujours sans réponse", "next_due": due.date().isoformat()})
        changed[oid] = (note, is_new)
        co = offers[oid].get("company") or oid
        events.append(f"{co} — candidature enregistrée" + (" (offre ajoutée)" if oid in created else ""))
    return {"offers": created, "notes": changed, "events": events}


# 3. Notation ------------------------------------------------------------------
def _style(config: dict[str, Any]) -> str:
    if config.get("lang") == "en":
        return "in clear professional English"
    return "en français soutenu, sans le pronom « on »"



def score(config: dict[str, Any], learned: dict[str, Any], items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not items:
        return []
    out: list[dict[str, Any]] = []
    for i in range(0, len(items), 15):
        batch = items[i : i + 15]
        prompt = f"""Note chaque offre sur 100 pour ce candidat.

CRITÈRES EXPLICITES (priment toujours)
{json.dumps({k: config.get(k) for k in ['salary_min_k','home_address','geo','roles','domains','contracts','exclusions','weights','partners','free']}, ensure_ascii=False)}

TENDANCES APPRISES DE SES CHOIX (ajustement ±10 au plus ; mentionne « Ajusté selon vos choix : … » dans reasons si appliqué)
{json.dumps(learned.get('lessons', []), ensure_ascii=False)}

OFFRES
{json.dumps(batch, ensure_ascii=False)}

Pour chaque offre, dans le même ordre : écarte (exclude=true) ce que les exclusions interdisent ; sinon donne
score, tier (« match » ≥ 70 sans point bloquant, « maybe » 50-69 ou point bloquant négociable, « far » pour
une offre éloignée mais originale), breakdown (détail du score : geo sur 30, tech sur 30, seniority sur 15,
salary sur 15, stability sur 10), reasons (1 à 2 phrases, {_style(config)}), blockers (ou vide),
kind (« emploi » ou « associe »), complète location, contract, remote, salary si l'annonce les donne,
et donne lat/lon (WGS84 approximatif de la ville du poste ; null si télétravail complet ou lieu inconnu).
Format : [{{"exclude": bool, "score": int, "tier": str, "breakdown": {{"geo": int, "tech": int, "seniority": int,
"salary": int, "stability": int}}, "reasons": str, "blockers": str, "kind": str, "location": str, "contract": str,
"remote": str, "salary": str, "lat": float|null, "lon": float|null}}]"""
        try:
            res = llm.complete_json(prompt, tier="complex")
        except Exception as e:  # noqa: BLE001
            log.warning("Notation impossible : %s", e)
            continue
        for item, r in zip(batch, res if isinstance(res, list) else []):
            if not isinstance(r, dict) or r.get("exclude"):
                continue
            merged = {**item, **{k: v for k, v in r.items() if v not in (None, "") and k != "exclude"}}
            out.append(merged)
    # Au plus 3 offres « plus éloignées » par passage
    far = [o for o in out if o.get("tier") == "far"]
    far.sort(key=lambda o: -int(o.get("score") or 0))
    drop = {id(o) for o in far[3:]}
    return [o for o in out if id(o) not in drop]


def score_pending(store: Store, config: dict[str, Any], learned: dict[str, Any], fetch=None, limit: int = 15) -> int:
    """Note les offres « à évaluer » (ajouts manuels, candidatures directes) ; l'annonce est lue si besoin."""
    fetch = fetch or _fetch_text
    todo = [d["data"] for d in store.list("offers") if (d["data"].get("tier") in (None, "", "pending")) and d["data"].get("id")][:limit]
    if not todo:
        return 0
    items = []
    for o in todo:
        it = {k: o.get(k) for k in ("id", "title", "company", "location", "url", "raw_text", "contract", "remote", "salary")}
        url = o.get("url") or ""
        if url.startswith("http") and not any(d in url for d in NO_FETCH) and len(o.get("raw_text") or "") < 400:
            try:
                it["posting_excerpt"] = fetch(url)[:6000]
            except Exception as e:  # noqa: BLE001
                log.info("Annonce illisible %s : %s", url, e)
        items.append(it)
    n = 0
    for r in score(config, learned, items):
        oid = r.get("id")
        if not oid:
            continue
        patch = {k: r[k] for k in ("score", "tier", "breakdown", "reasons", "blockers", "location", "contract", "remote", "salary", "lat", "lon") if r.get(k) not in (None, "")}
        if patch.get("tier"):
            store.update("offers", oid, patch)
            n += 1
    return n


# 4. Pistes complémentaires (freelance, international, ...) -----------------------
TRACK_KEYS = ("roles", "domains", "geo", "contracts", "exclusions", "free")


def tracks_due(config: dict[str, Any], now: datetime | None = None, force: bool = False) -> list[dict[str, Any]]:
    """Pistes actives à traiter maintenant : quotidiennes chaque jour, hebdomadaires le lundi."""
    now = now or datetime.now()
    out = []
    for t in config.get("tracks") or []:
        if not t.get("id") or not t.get("active"):
            continue
        if force or t.get("frequency", "weekly") == "daily" or now.weekday() == 0:
            out.append(t)
    return out


def track_config(config: dict[str, Any], track: dict[str, Any]) -> dict[str, Any]:
    """Configuration de notation propre à une piste : ses critères remplacent ceux du fil principal."""
    tc = {k: v for k, v in config.items() if k not in ("tracks", "sources", "partners")}
    for k in TRACK_KEYS:
        tc[k] = track.get(k) or ""
    tc["salary_min_k"] = None
    pay = (track.get("pay") or "").strip()
    tc["free"] = "\n".join(x for x in [f"Piste « {track.get('name', track['id'])} ».", f"Rémunération attendue : {pay}." if pay else "", tc["free"]] if x)
    tc["sources"] = [s for s in track.get("sources") or [] if s.get("active", True)]
    tc["partners"] = ""
    return tc


def run_tracks(config: dict[str, Any], learned: dict[str, Any], known_urls: list[str], seen: set[str], force: bool = False) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for t in tracks_due(config, force=force):
        tc = track_config(config, t)
        if not tc["sources"]:
            continue
        cap = int(t.get("max_per_run") or 5)
        items = []
        for it in web.search(tc, known_urls, max_jobs=cap * 2, max_partners=0):
            k = dedupe_key(it)
            if it.get("title") and it.get("url") and k not in seen:
                seen.add(k)
                items.append(it)
        scored = [o for o in score(tc, {"lessons": []}, items[: cap * 2]) if o.get("tier") in ("match", "maybe")]
        scored.sort(key=lambda o: -int(o.get("score") or 0))
        for o in scored[:cap]:
            o["track"] = t["id"]
            o["kind"] = "associe" if t["id"] == "associes" else "emploi"
            found.append(o)
    return found


# 5. Conservation du texte des annonces étudiées --------------------------------
STUDIED = {"creuser", "postule", "entretien", "offre"}
NO_FETCH = ("linkedin.com", "indeed.", "glassdoor.")


def _fetch_text(url: str) -> str:
    r = httpx.get(url, timeout=20, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (Huntboard; personal job search)"})
    r.raise_for_status()
    return email_imap.html_to_text(r.text)


def keep_postings(store: Store, offers: dict[str, dict], notes: dict[str, dict], fetch=_fetch_text, max_attempts: int = 3) -> int:
    """Conserve le texte complet des annonces au moins « à creuser » (une fois récupéré, il n'est plus modifié)."""
    kept = 0
    for oid, n in notes.items():
        o = offers.get(oid)
        if not o or n.get("status") not in STUDIED:
            continue
        cur = store.data("postings", oid) or {}
        if cur.get("text") or int(cur.get("attempts") or 0) >= max_attempts:
            continue
        url = o.get("url") or ""
        text = ""
        if url.startswith("http") and not any(d in url for d in NO_FETCH):
            try:
                text = fetch(url)
            except Exception as e:  # noqa: BLE001
                log.info("Annonce illisible %s : %s", url, e)
        if len(text) >= 400:
            store.set("postings", oid, {"offer_id": oid, "url": url, "text": text[:40000], "fetched_at": now_iso(), "method": "web", "status": "ok"})
            kept += 1
        else:
            store.set("postings", oid, {"offer_id": oid, "url": url, "status": "unavailable", "attempts": int(cur.get("attempts") or 0) + 1, "fetched_at": now_iso()})
    return kept


# 6. Message du jour sans nouveauté (encourageant, factuel, traduit) ------------
EMPTY = {
    "fr": [
        "Pas de nouvelle offre ce matin. {active} candidature(s) restent en cours : une relance ciblée ou un message à une personne de votre réseau peut faire avancer la semaine.",
        "Rien de neuf aujourd'hui sur vos sources. Les meilleures opportunités passent souvent par le réseau : un contact pris aujourd'hui compte autant qu'une offre trouvée.",
        "Aucune annonce nouvelle ce matin. Le moment est bon pour préparer un entretien, mettre à jour une lettre ou relire une offre « à creuser ».",
    ],
    "en": [
        "No new offers this morning. {active} application(s) are still open: a targeted follow-up or a message to someone in your network can move the week forward.",
        "Nothing new on your sources today. The best opportunities often come through people: a contact made today counts as much as an offer found.",
        "No new postings this morning. A good moment to prepare an interview, update a letter or review an offer marked to explore.",
    ],
}


def empty_message(config: dict[str, Any], notes: dict[str, dict], day: datetime | None = None) -> str:
    day = day or datetime.now()
    msgs = EMPTY["en" if config.get("lang") == "en" else "fr"]
    active = sum(1 for n in notes.values() if n.get("status") in ("postule", "entretien", "offre"))
    return msgs[day.toordinal() % len(msgs)].format(active=active)


# 6 bis. Sources : vérification et suggestions adaptées au profil ---------------
SUGG_DOC = ("sources", "suggestions")


def _probe(url: str) -> dict[str, Any]:
    r = httpx.get(url, timeout=15, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (Huntboard; personal job search)"})
    m = re.search(r"<title[^>]*>(.*?)</title>", r.text[:20000], re.I | re.S)
    return {"code": r.status_code, "final_url": str(r.url), "title": re.sub(r"\s+", " ", m.group(1)).strip()[:160] if m else ""}


def check_source(item: dict[str, Any], probe=_probe) -> dict[str, Any]:
    """Teste l'adresse d'une source : ok, moved (redirigée ailleurs), blocked (refus aux robots) ou unreachable."""
    url = (item.get("url") or "").strip()
    out = {**item, "checked_at": now_iso()}
    if not url.startswith("http"):
        out["status"] = "no_url"
        return out
    if any(d in url for d in NO_FETCH):
        out["status"] = "not_checked"  # plateformes jamais lues directement
        return out
    try:
        r = probe(url)
    except Exception:  # noqa: BLE001
        out["status"] = "unreachable"
        return out
    code = int(r.get("code") or 0)
    if code in (401, 403, 429):
        out["status"] = "blocked"
    elif code >= 400 or code == 0:
        out["status"] = "unreachable"
    else:
        host = lambda u: re.sub(r"^www\.", "", httpx.URL(u).host or "")  # noqa: E731
        moved = host(r.get("final_url") or url) != host(url)
        out["status"] = "moved" if moved else "ok"
        if moved:
            out["url"] = r.get("final_url")
        if r.get("title"):
            out["title"] = r["title"]
    return out


def source_yield(config: dict[str, Any], offers: dict[str, dict], notes: dict[str, dict]) -> list[dict[str, Any]]:
    """Rendement de chaque source active : offres trouvées et offres retenues (au moins « à creuser »)."""
    rows = []
    for src in config.get("sources") or []:
        key = _norm(src.get("name", "")).split(" (")[0]
        words = [w for w in key.split() if len(w) >= 4][:2] or key.split()[:1]
        hits = [oid for oid, o in offers.items() if not o.get("track") and words and all(w in _norm(o.get("source") or "") for w in words)]
        kept = sum(1 for oid in hits if (notes.get(oid) or {}).get("status") in POSITIVE)
        rows.append({"name": src.get("name"), "active": src.get("active", True), "found": len(hits), "kept": kept})
    return rows


def _suggest_prompt(config: dict[str, Any], cv: str, yields: list[dict[str, Any]], n: int, web: bool) -> str:
    tracks = [{"id": t.get("id"), "name": t.get("name"), "sources": [x.get("name") for x in t.get("sources") or []]} for t in config.get("tracks") or []]
    lang = "English" if config.get("lang") == "en" else "French (formal register, never the pronoun « on »)"
    return f"""You help a job seeker choose where their daily job watch should look.
Suggest up to {n} NEW sources (job boards, specialised networks, recruitment firms, employers' career pages,
co-founder matching services, public programmes) that fit THIS person, then list the current sources that look
useless. {"Use web search to confirm each source exists and to give its official page." if web else "Give only sources you are confident exist; leave url empty when unsure of the exact address."}
Never suggest LinkedIn scraping or sites that need the person's login to list offers.

PROFILE AND CRITERIA
{json.dumps({k: config.get(k) for k in ("country", "home_address", "geo", "roles", "domains", "contracts", "exclusions", "free")}, ensure_ascii=False)[:6000]}
CV (excerpt)
{cv[:5000]}
CURRENT MAIN SOURCES WITH YIELD (found = offers collected, kept = offers the person kept)
{json.dumps(yields, ensure_ascii=False)[:5000]}
EXTRA TRACKS (target a track by its id when the source belongs there)
{json.dumps(tracks, ensure_ascii=False)[:3000]}

Write "note" (how the watch should read the source) and "why" (one sentence on why it fits this person) in {lang}.
JSON: {{"suggestions": [{{"name": str, "url": str, "note": str, "why": str, "target": "main" or a track id}}],
"weak": [{{"name": str, "why": str}}]}}"""


def suggest_sources(config: dict[str, Any], cv: str, yields: list[dict[str, Any]], n: int = 6) -> dict[str, Any]:
    """Suggestions de sources : avec la recherche web (Anthropic) si possible, sinon d'après les connaissances du modèle."""
    try:
        return llm.web_research_json(_suggest_prompt(config, cv, yields, n, True), country=config.get("country") or "FR") or {}
    except Exception as e:  # noqa: BLE001 - pas de recherche web : connaissances du modèle, adresses testées ensuite
        log.info("Suggestion de sources sans recherche web : %s", e)
        return llm.complete_json(_suggest_prompt(config, cv, yields, n, False), tier="default") or {}


def merge_suggestions(current: dict[str, Any], items: list[dict[str, Any]], config: dict[str, Any], origin: str) -> dict[str, Any]:
    """Ajoute des suggestions sans doublon (déjà en source ou déjà suggérée) ; met à jour celles qui existent."""
    have = {_norm(x.get("name", "")) for x in config.get("sources") or []}
    for t in config.get("tracks") or []:
        have |= {_norm(x.get("name", "")) for x in t.get("sources") or []}
    out = list(current.get("items") or [])
    idx = {_norm(x.get("name", "")): i for i, x in enumerate(out)}
    for it in items:
        k = _norm(it.get("name", ""))
        if not k or k in have:
            continue
        if k in idx:
            out[idx[k]] = {**out[idx[k]], **{a: b for a, b in it.items() if b not in (None, "")}}
        else:
            idx[k] = len(out)
            out.append({"origin": origin, "target": "main", "status": "unverified", "created_at": now_iso(), **it})
    return {**current, "items": out, "updated_at": now_iso()}


def verify_and_suggest(store: Store, items: list[dict[str, Any]] | None = None, more: int = 0,
                       origin: str = "web", probe=_probe) -> dict[str, Any]:
    """Vérifie les adresses des suggestions (toutes ou celles passées) et, si demandé, en cherche d'autres."""
    config = store.data("config", "main") or {}
    cur = store.data(*SUGG_DOC) or {}
    new: list[dict[str, Any]] = []
    weak: list[dict[str, Any]] = []
    if more and settings.llm_enabled:
        offers = {d["id"]: d["data"] for d in store.list("offers")}
        notes = {d["id"]: d["data"] for d in store.list("notes")}
        cv = (store.data("profile", "cv") or {}).get("text", "")
        try:
            res = suggest_sources(config, cv, source_yield(config, offers, notes), more)
            new = [x for x in res.get("suggestions") or [] if isinstance(x, dict) and x.get("name")]
            weak = [x for x in res.get("weak") or [] if isinstance(x, dict) and x.get("name")]
        except Exception as e:  # noqa: BLE001
            log.warning("Suggestion de sources impossible : %s", e)
    doc = merge_suggestions(cur, list(items or []) + new, config, origin)
    names = {_norm(x.get("name", "")) for x in (items or [])} if items else None
    doc["items"] = [check_source(x, probe) if (names is None or _norm(x.get("name", "")) in names or x.get("status") == "unverified") else x for x in doc["items"]]
    if weak:
        doc["weak"] = weak
    doc["verify"] = {"state": "done", "done_at": now_iso(), "by": "app"}
    store.set(*SUGG_DOC, doc)
    return doc


# 7. Orchestration -------------------------------------------------------------
def run(store: Store, mail_days: int | None = None) -> str:
    run_id = store.start_run()
    try:
        config = store.data("config", "main") or {}
        offers = {d["id"]: d["data"] for d in store.list("offers")}
        notes = {d["id"]: d["data"] for d in store.list("notes")}
        known = {dedupe_key(o) for o in offers.values()}
        known_urls = [o.get("url", "") for o in offers.values() if o.get("url")]

        learned = learn(store, offers, notes)
        days = mail_days or (4 if datetime.now().weekday() == 0 else 2)
        mail_items, events = offers_from_mail(days)
        web_items = web.search(config, known_urls)

        fresh, seen = [], set(known)
        for it in mail_items + web_items:
            if not it.get("title") or not it.get("url"):
                continue
            k = dedupe_key(it)
            if k in seen:
                continue
            seen.add(k)
            fresh.append(it)

        scored = score(config, learned, fresh[:40])
        jobs = sorted([o for o in scored if o.get("kind") != "associe"], key=lambda o: -int(o.get("score") or 0))[:25]
        partners = sorted([o for o in scored if o.get("kind") == "associe"], key=lambda o: -int(o.get("score") or 0))[:5]
        extra = run_tracks(config, learned, known_urls, seen, force=bool(mail_days))
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        for o in jobs + partners + extra:
            oid = slug(o.get("company", ""), o.get("title", ""))
            if store.get("offers", oid):
                oid = f"{oid}-{dedupe_key(o)[-6:]}"
            o.update({"id": oid, "found_at": stamp, "kind": o.get("kind") or "emploi"})
            store.set("offers", oid, o)

        if settings.imap_enabled:
            try:
                acks = [m for m in email_imap.fetch_matching(days, ack_header) if is_ack(m)]
                res = application_acks(acks, offers, notes)
                for oid, o in res["offers"].items():
                    store.set("offers", oid, o)
                    offers[oid] = o
                for oid, (note, is_new) in res["notes"].items():
                    if is_new:
                        store.set("notes", oid, note)
                    else:
                        store.update("notes", oid, {k: note[k] for k in ("events", "updated_at")})
                events.extend(res["events"])
            except Exception as e:  # noqa: BLE001
                log.warning("Lecture des accusés de candidature impossible : %s", e)

        scored_pending = score_pending(store, config, learned)
        offers = {d["id"]: d["data"] for d in store.list("offers")}
        notes = {d["id"]: d["data"] for d in store.list("notes")}

        if settings.follow_ups and settings.imap_enabled:
            try:
                heads = [m for m in email_imap.fetch_headers(days) if not (ack_header(m.sender, m.subject) and ACK_RE.search(m.subject or ""))]
                fresh_events = follow_up_events(heads, offers, notes, settings.alert_senders)
                for oid, evs in fresh_events.items():
                    n = store.data("notes", oid) or {}
                    store.update("notes", oid, {"events": (n.get("events") or []) + evs})
                    co = (offers.get(oid) or {}).get("company") or oid
                    events.extend(f"{co} — {e['text']}" for e in evs)
            except Exception as e:  # noqa: BLE001
                log.warning("Suivi des e-mails impossible : %s", e)
        kept = keep_postings(store, offers, notes)
        if datetime.now().weekday() == 0 and settings.llm_enabled:
            try:
                before = {_norm(x.get("name", "")) for x in (store.data(*SUGG_DOC) or {}).get("items") or []}
                doc = verify_and_suggest(store, items=[], more=2, origin="watch")
                fresh_src = [x for x in doc.get("items") or [] if _norm(x.get("name", "")) not in before and x.get("status") in ("ok", "moved", "not_checked")]
                if fresh_src:
                    events.append(("Sources suggérées : " if config.get("lang") != "en" else "Suggested sources: ") + ", ".join(x["name"] for x in fresh_src[:2]))
            except Exception as e:  # noqa: BLE001
                log.warning("Suggestion hebdomadaire de sources impossible : %s", e)
        summary = _summary(jobs, partners, events) if (jobs or partners or events or extra) else empty_message(config, notes)
        if scored_pending:
            summary += f"\n{scored_pending} offre(s) ajoutée(s) à la main ou par candidature notée(s)." if config.get("lang") != "en" else f"\n{scored_pending} manually added offer(s) scored."
        if kept:
            summary += f"\n{kept} texte(s) d'annonce conservé(s)." if config.get("lang") != "en" else f"\n{kept} posting text(s) kept."
        if extra:
            summary += f"\nPistes complémentaires : {len(extra)} offre(s), à consulter dans leur filtre."
        store.finish_run(run_id, "ok", summary)
        notify(summary)  # chaque matin : nouveautés, ou message d'encouragement si rien de neuf
        return summary
    except Exception as e:  # noqa: BLE001
        log.exception("Échec du passage de veille")
        store.finish_run(run_id, "erreur", str(e))
        raise


def _summary(jobs: list[dict], partners: list[dict], events: list[str]) -> str:
    if not jobs and not partners and not events:
        return "Veille du jour : rien de nouveau."
    by = {t: sum(1 for o in jobs if o.get("tier") == t) for t in ("match", "maybe", "far")}
    lines = [f"Veille du jour : {len(jobs)} offres ({by['match']} correspondent, {by['maybe']} possibles, {by['far']} éloignées), {len(partners)} recherches d'associés."]
    for o in jobs[:3]:
        lines.append(f"• {o.get('company')} — {o.get('title')} ({o.get('score')})")
    if events:
        lines.append("À noter : " + " ; ".join(events[:4]))
    return "\n".join(lines)


def notify(text: str) -> None:
    if not settings.notify_url:
        return
    try:
        httpx.post(settings.notify_url, content=text.encode("utf-8"), headers={"Title": "Huntboard"}, timeout=10)
    except Exception as e:  # noqa: BLE001
        log.warning("Notification impossible : %s", e)
