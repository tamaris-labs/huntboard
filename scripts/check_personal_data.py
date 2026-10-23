#!/usr/bin/env python3
"""Détecte les données personnelles avant publication du dépôt.

Vérifie tous les fichiers suivis par Git (et, avec --history, tout l'historique) :
- adresses e-mail et numéros de téléphone français ;
- termes interdits listés dans `.personal-data-denylist` (un par ligne : votre nom,
  ville, entreprises de vos candidatures, noms de contacts…). Ce fichier est ignoré
  par Git : il ne quitte jamais votre machine.

Code de sortie 1 si quelque chose est trouvé.
Usage : python scripts/check_personal_data.py [--history]
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DENYLIST = ROOT / ".personal-data-denylist"

ALLOWED_EMAILS = {
    "jobalerts-noreply@linkedin.com",
    "jobs-noreply@linkedin.com",
    "noreply@anthropic.com",
}
EMAIL = re.compile(r"\b[A-Za-z0-9][\w.+-]*@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b")
PHONE = re.compile(r"(?<!\d)(?:\+33\s?|0)[1-9](?:[\s.-]?\d{2}){4}(?!\d)")


def tracked_files() -> list[Path]:
    try:
        out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        return [ROOT / p for p in out.splitlines()]
    except Exception:  # noqa: BLE001 - dépôt pas encore initialisé
        return [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and "data" not in p.parts]


def scan(name: str, text: str, terms: list[str]) -> list[str]:
    hits = []
    for m in EMAIL.finditer(text):
        if m.group(0).lower() not in ALLOWED_EMAILS and not m.group(0).endswith(("example.com", "exemple.fr")):
            hits.append(f"{name}: e-mail « {m.group(0)} »")
    for m in PHONE.finditer(text):
        digits = re.sub(r"\D", "", m.group(0)).replace("33", "0", 1) if m.group(0).startswith("+") else re.sub(r"\D", "", m.group(0))
        if digits.startswith("019900"):  # plage réservée à la fiction (ARCEP) : données de démonstration
            continue
        hits.append(f"{name}: téléphone « {m.group(0)} »")
    low = text.lower()
    for t in terms:
        if t.lower() in low:
            hits.append(f"{name}: terme interdit « {t} »")
    return hits


def main() -> int:
    terms = []
    if DENYLIST.exists():
        terms = [t.strip() for t in DENYLIST.read_text(encoding="utf-8").splitlines() if t.strip() and not t.startswith("#")]
    else:
        print("Conseil : créez .personal-data-denylist avec vos noms, villes et entreprises à ne jamais publier.")
    hits: list[str] = []
    for f in tracked_files():
        if f.name == DENYLIST.name or f.suffix in {".png", ".jpg", ".ico", ".zip"}:
            continue
        try:
            hits += scan(str(f.relative_to(ROOT)), f.read_text(encoding="utf-8"), terms)
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    if "--history" in sys.argv:
        log = subprocess.run(["git", "log", "-p", "--all"], cwd=ROOT, capture_output=True, text=True).stdout
        hits += scan("historique Git", log, terms)
    for h in hits:
        print("⚠", h)
    print(f"{len(hits)} élément(s) suspect(s).")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
