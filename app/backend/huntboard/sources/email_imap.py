"""Lecture des alertes emploi reçues par e-mail (IMAP, en lecture seule).

Fonctionne avec Gmail (mot de passe d'application), Outlook, Fastmail ou toute
messagerie IMAP. Rien n'est modifié dans la boîte : la connexion est ouverte en
lecture seule (EXAMINE), sans marquer les messages comme lus.
"""

from __future__ import annotations

import email
import imaplib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime

from ..settings import settings


@dataclass
class Mail:
    sender: str
    subject: str
    date: str
    text: str


def _decode(value: str | None) -> str:
    return str(make_header(decode_header(value or "")))


def html_to_text(html: str) -> str:
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):  # conserve les liens dans le texte
            a.append(f" <{a['href']}>")
        return soup.get_text(" ")
    except Exception:  # noqa: BLE001 - repli sans dépendance
        return re.sub(r"<[^>]+>", " ", html)


def _body(msg: email.message.Message) -> str:
    plain, html = "", ""
    for part in msg.walk() if msg.is_multipart() else [msg]:
        ctype = part.get_content_type()
        if part.get_filename():
            continue
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        txt = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        if ctype == "text/plain" and not plain:
            plain = txt
        elif ctype == "text/html" and not html:
            html = txt
    text = plain or html_to_text(html)
    return re.sub(r"[͏­‌\s]+", " ", text).strip()


def fetch_headers(days: int = 2, limit: int = 400) -> list[Mail]:
    """En-têtes (expéditeur, objet, date) des e-mails récents, sans le corps ni marquage comme lu."""
    if not settings.imap_enabled:
        return []
    since = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
    out: list[Mail] = []
    with imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port) as box:
        box.login(settings.imap_user, settings.imap_password)
        box.select(settings.imap_folder, readonly=True)
        typ, data = box.search(None, "SINCE", since)
        ids = data[0].split() if typ == "OK" and data and data[0] else []
        for mid in ids[-limit:]:
            typ, d = box.fetch(mid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
            if typ != "OK" or not d or not isinstance(d[0], tuple):
                continue
            msg = email.message_from_bytes(d[0][1])
            try:
                date = parsedate_to_datetime(msg.get("Date")).isoformat()
            except Exception:  # noqa: BLE001
                date = ""
            out.append(Mail(_decode(msg.get("From")), _decode(msg.get("Subject")), date, ""))
    return out


def fetch_alerts(days: int = 2, senders: list[str] | None = None, limit: int = 60) -> list[Mail]:
    if not settings.imap_enabled:
        return []
    senders = senders or settings.alert_senders
    since = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
    out: list[Mail] = []
    with imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port) as box:
        box.login(settings.imap_user, settings.imap_password)
        box.select(settings.imap_folder, readonly=True)
        ids: list[bytes] = []
        for s in senders:
            typ, data = box.search(None, "SINCE", since, "FROM", f'"{s}"')
            if typ == "OK" and data and data[0]:
                ids.extend(data[0].split())
        for mid in sorted(set(ids), key=int, reverse=True)[:limit]:
            typ, data = box.fetch(mid, "(BODY.PEEK[])")
            if typ != "OK" or not data or not isinstance(data[0], tuple):
                continue
            msg = email.message_from_bytes(data[0][1])
            try:
                date = parsedate_to_datetime(msg.get("Date")).isoformat()
            except Exception:  # noqa: BLE001
                date = ""
            out.append(Mail(_decode(msg.get("From")), _decode(msg.get("Subject")), date, _body(msg)))
    return out


_LI_VIEW = re.compile(r"linkedin\.com/comm/jobs/view/(\d+)")


def parse_linkedin_alert(text: str) -> list[dict[str, str]]:
    """Extraction déterministe des offres d'un e-mail d'alerte LinkedIn.

    Renvoie [{title_block, linkedin_id, url}] où title_block contient l'intitulé,
    l'entreprise et le lieu tels qu'affichés ; la mise en forme fine est confiée au LLM.
    """
    clean = re.sub(r"\s+", " ", text)
    found: dict[str, dict[str, str]] = {}
    for m in re.finditer(r"Voir l[’']offre d[’']emploi\s*:?\s*<?(https?://\S+)", clean):
        idm = _LI_VIEW.search(m.group(1))
        if not idm or idm.group(1) in found:
            continue
        before = re.sub(r"<?https?://\S+>?", " ", clean[max(0, m.start() - 600) : m.start()])
        before = re.sub(r"\s+", " ", before).strip()[-220:]
        found[idm.group(1)] = {
            "title_block": before,
            "linkedin_id": idm.group(1),
            "url": f"https://www.linkedin.com/jobs/view/{idm.group(1)}/",
        }
    return list(found.values())
