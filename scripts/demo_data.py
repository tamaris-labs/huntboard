#!/usr/bin/env python3
"""Remplit une base Huntboard avec des données de démonstration entièrement fictives.

Sert aux captures d'écran et à l'essai de l'application sans compte ni données réelles.
Usage : HUNTBOARD_DATA_DIR=./demo-data python scripts/demo_data.py
puis : HUNTBOARD_DATA_DIR=./demo-data uvicorn huntboard.main:app (depuis app/backend)
Données en anglais : HUNTBOARD_DEMO_LANG=en (même scénario, textes traduits).
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app" / "backend"))
from huntboard.store import Store  # noqa: E402

data_dir = Path(os.environ.get("HUNTBOARD_DATA_DIR", "./demo-data"))
data_dir.mkdir(parents=True, exist_ok=True)
st = Store(str(data_dir / "huntboard.sqlite3"))
now = datetime.now(timezone.utc)
iso = lambda d=0, h=0: (now - timedelta(days=d, hours=h)).isoformat(timespec="seconds")  # noqa: E731
day = lambda d: (now + timedelta(days=d)).strftime("%Y-%m-%d")  # noqa: E731
EN = os.environ.get("HUNTBOARD_DEMO_LANG", "fr").lower().startswith("en")
L = lambda fr, en: en if EN else fr  # noqa: E731

cfg = json.loads((ROOT / "kit/skills/huntboard/config.example.json").read_text(encoding="utf-8"))
cfg.update({
    "lang": L("fr", "en"), "country": "FR", "onboarded": True, "demo": True, "salary_min_k": 60,
    "home_address": L("Nantes (quartier Île de Nantes)", "Nantes (Île de Nantes district)"),
    "geo": L("Domicile : Nantes.\nTrajet de 30 min ou moins : présentiel accepté.\nAu-delà : 2 jours de télétravail minimum.\nTélétravail total accepté partout en France.",
             "Home: Nantes.\nCommute of 30 min or less: on-site accepted.\nBeyond: at least 2 remote days.\nFully remote accepted anywhere in France."),
    "roles": L("Product manager senior\nEngineering manager\nResponsable produit IA\nChef de projet data", "Senior product manager\nEngineering manager\nAI product lead\nData project manager"),
    "domains": L("IA appliquée, data, logiciels B2B, énergie", "Applied AI, data, B2B software, energy"),
    "contracts": L("CDI ; freelance à étudier", "Permanent; freelance considered"), "exclusions": L("Stages, alternances, postes juniors", "Internships, apprenticeships, junior roles"),
    "profile": L("Profil fictif de démonstration : quinze ans dans le logiciel B2B, dont huit en management d'équipes produit et techniques (jusqu'à 25 personnes). Lancement de trois produits SaaS, mise en place d'une démarche produit pilotée par la donnée, projets d'IA appliquée (classification de documents, prévision de la demande). Recherche un poste de responsable produit ou d'engineering manager, de préférence en IA ou dans l'énergie.",
                 "Fictional demo profile: fifteen years in B2B software, eight of them managing product and engineering teams (up to 25 people). Launched three SaaS products, set up data-driven product practices, applied AI projects (document classification, demand forecasting). Looking for a product lead or engineering manager role, preferably in AI or energy."),
    "tracks": [{"id": "freelance", "name": L("Missions freelance", "Freelance assignments"), "active": True, "in_main": False, "notify": False,
                "frequency": "weekly", "max_per_run": 5, "roles": L("Product management à temps partagé", "Part-time product management"), "contracts": "Freelance", "pay": L("TJM 600 €", "€600 day rate"), "sources": []},
               {"id": "associes", "name": L("Associés et cofondateurs", "Partners and co-founders"), "active": True, "in_main": True, "notify": False,
                "frequency": "daily", "max_per_run": 5, "roles": L("CTO associé", "Co-founder CTO"), "contracts": L("Association", "Partnership"), "sources": []}],
})
st.set("config", "main", cfg)
st.set("profile", "cv", {"text": L("CV fictif de démonstration. ", "Fictional demo CV. ") * 40, "filename": "cv-demo.pdf"})

REMOTE = L("Télétravail", "Remote")
OFFERS = [
    ("aurora-energie-head-of-product", L("Head of Product énergie", "Head of Product, Energy"), "Aurora Énergie", "Nantes", 47.218, -1.553, 88, "match", "postule"),
    ("nordline-em-plateforme", L("Engineering Manager plateforme", "Platform Engineering Manager"), "Nordline Robotics", "Saint-Herblain", 47.212, -1.649, 84, "match", "entretien"),
    ("aster-analytics-pm-ia", L("Product Manager IA", "AI Product Manager"), "Aster Analytics", "Rennes", 48.117, -1.678, 81, "match", "creuser"),
    ("blue-harbor-cpo", "Chief Product Officer", "Blue Harbor", REMOTE, None, None, 79, "match", "nouvelle"),
    ("kerlan-data-lead", L("Responsable data et IA", "Head of Data and AI"), "Kerlan Logistique", "Vannes", 47.658, -2.760, 74, "maybe", "nouvelle"),
    ("solea-chef-projet-data", L("Chef de projet data", "Data Project Manager"), "Soléa Mobilité", "Angers", 47.478, -0.563, 70, "match", "creuser"),
    ("verdane-po-senior", L("Product Owner senior", "Senior Product Owner"), "Verdane", "Paris", 48.857, 2.352, 68, "maybe", "nouvelle"),
    ("orbis-em", "Engineering Manager", "Orbis Santé", "Bordeaux", 44.838, -0.579, 63, "maybe", "nouvelle"),
    ("lumen-pm-b2b", L("Product Manager B2B", "B2B Product Manager"), "Lumen Software", "La Roche-sur-Yon", 46.670, -1.426, 72, "match", "nouvelle"),
    ("tidal-ai-cofounder", L("CTO associé IA climat", "Co-founder CTO, climate AI"), L("Tidal (projet en création)", "Tidal (early-stage project)"), "Nantes", 47.218, -1.553, 66, "maybe", "nouvelle"),
    ("granit-pm", "Product Manager", "Granit Assurances", "Brest", 48.390, -4.486, 55, "far", "ecartee"),
]
for oid, title, co, loc, lat, lon, score, tier, status in OFFERS:
    partner = oid == "tidal-ai-cofounder"
    st.set("offers", oid, {
        "id": oid, "title": title, "company": co, "location": loc, "lat": lat, "lon": lon, "score": score, "tier": tier,
        "kind": "associe" if partner else "emploi", "track": "associes" if partner else None,
        "contract": L("CDI", "Permanent"), "remote": (L("2 jours", "2 days") if loc != REMOTE else L("Total", "Full")),
        "salary": "65-75 k€" if score > 70 else L("non affiché", "not shown"),
        "url": "https://jobs.example.com/" + oid, "source": L("Démonstration", "Demo"),
        "breakdown": {"geo": round(score * .3), "tech": round(score * .3), "seniority": round(score * .15), "salary": round(score * .15), "stability": score - round(score * .3) * 2 - round(score * .15) * 2},
        "reasons": L("Offre fictive de démonstration : rôle produit senior en IA appliquée, cohérent avec le profil.", "Fictional demo offer: senior product role in applied AI, consistent with the profile."),
        "blockers": "" if tier == "match" else L("Télétravail à confirmer", "Remote work to be confirmed"), "found_at": iso(len(oid) % 9, 3),
        "raw_text": L("Annonce fictive : pilotage d'une équipe produit, feuille de route, discovery et livraison.", "Fictional posting: lead a product team, roadmap, discovery and delivery."),
    })
    if status != "nouvelle":
        note = {"status": status, "updated_at": iso(1), "events": [{"at": iso(6), "text": L("À creuser", "To explore")}]}
        if status in ("postule", "entretien"):
            note.update(applied_at=day(-5), events=note["events"] + [{"at": iso(5), "text": L("Candidature envoyée", "Application sent")}])
        if status == "entretien":
            note.update(interview_at=day(3) + "T10:00", next_action=L("Préparer l'étude de cas", "Prepare the case study"), next_due=day(2),
                        contacts=[{"name": "Camille Durand", "role": "Talent acquisition", "company": co,
                                   "email": "camille.durand@example.com", "phone": "01 99 00 12 34", "added_at": iso(4)}])
        st.set("notes", oid, note)
st.set("postings", "nordline-em-plateforme", {"offer_id": "nordline-em-plateforme", "url": "https://jobs.example.com/nordline", "method": "web", "status": "ok", "fetched_at": iso(2),
                                              "text": L("Engineering Manager plateforme (annonce fictive)\n\nMissions : animer deux équipes, fiabiliser la plateforme robotique, recruter.\nProfil : management d'équipes techniques, culture produit, intérêt pour l'IA embarquée.",
                                                                        "Platform Engineering Manager (fictional posting)\n\nDuties: lead two teams, make the robotics platform reliable, hire.\nProfile: engineering management, product mindset, interest in embedded AI.")})
st.set("memos", "m-demo1", {"id": "m-demo1", "text": L("Appel avec une ancienne collègue : Aurora Énergie recrute aussi un lead data, recontacter mardi.", "Call with a former colleague: Aurora Énergie is also hiring a data lead, follow up on Tuesday."), "created_at": iso(1), "source": "voice", "offer_id": "aurora-energie-head-of-product", "offer_label": "Aurora Énergie"})
st.set("coach", "momentum", {"goals": {"applied": 3, "triaged": 15, "network": 2}, "network": {}, "wins": [{"at": iso(2), "text": L("Recommandation obtenue pour Nordline Robotics", "Referral obtained for Nordline Robotics")}], "active_days": [day(-1), day(0)]})
st.set("geo", "cache", {"home": {"label": "Nantes", "lat": 47.205, "lon": -1.545, "src": cfg["home_address"]}, "places": {}})
st.set("geo", "basemap", {"url": "/basemap.json"})
SHEET_FR = """## L'entreprise et le poste
Nordline Robotics (fictive) fabrique des robots logistiques ; le poste pilote deux équipes plateforme.
- À vérifier : taille des équipes, budget de recrutement, place de l'IA embarquée dans la feuille de route.

## Vos arguments
- Fiabilisation d'une plateforme SaaS : disponibilité portée de 99,5 à 99,9 %.
- Recrutement et structuration d'une équipe de 12 personnes en 18 mois.

## Questions probables
1. Comment arbitrez-vous entre dette technique et nouvelles fonctions ?
2. Racontez un incident majeur et ce que vous en avez tiré.

## Questions à poser
- Quels indicateurs mesurent la réussite du poste à six mois ?
"""
SHEET_EN = """## The company and the role
Nordline Robotics (fictional) builds logistics robots; the role leads two platform teams.
- To check: team sizes, hiring budget, place of embedded AI in the roadmap.

## Your arguments
- Made a SaaS platform reliable: availability raised from 99.5% to 99.9%.
- Hired and structured a 12-person team in 18 months.

## Likely questions
1. How do you trade off technical debt against new features?
2. Tell us about a major incident and what you learned from it.

## Questions to ask
- Which indicators will measure success in the role after six months?
"""
st.set("prep", "nordline-em-plateforme", {"sheet": L(SHEET_FR, SHEET_EN), "updated_at": iso(1)})
assets_dir = data_dir / "assets"
assets_dir.mkdir(exist_ok=True)
pdf = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF"
for aid, name, kind, lang, text in [
    ("a" * 32, "CV Alex Martin (FR).pdf", "cv", "fr", "CV fictif."),
    ("b" * 32, "CV Alex Martin (EN).pdf", "cv", "en", "Fictional CV."),
    ("c" * 32, L("Lettre - Aurora Énergie - Head of Product (fr).txt", "Letter - Aurora Énergie - Head of Product (en).txt"), "letter", L("fr", "en"), L("Lettre fictive de démonstration.", "Fictional demo letter.")),
]:
    ctype = "application/pdf" if name.endswith(".pdf") else "text/plain"
    (assets_dir / aid).write_bytes(pdf if ctype == "application/pdf" else text.encode())
    (assets_dir / (aid + ".type")).write_text(ctype)
    st.set("documents", "d-" + aid[:6], {"id": "d-" + aid[:6], "name": name, "filename": name, "kind": kind, "lang": lang, "asset_id": aid,
                                          "size": 2048, "content_type": ctype, "created_at": iso(3), "text": text})
st.set("config", "learned", {"lessons": [
    {"text": L("Les postes d'engineering manager en entreprise industrielle sont retenus plus souvent que ceux des ESN.", "Engineering manager roles in industrial companies are kept more often than those at IT consultancies."),
     "effect": "+5", "evidence": L("4 offres retenues, 2 écartées pour « ESN »", "4 offers kept, 2 discarded for « consultancy »")},
    {"text": L("Les offres sans télétravail au-delà de 40 minutes de trajet sont écartées.", "Offers with no remote work beyond a 40-minute commute are discarded."),
     "effect": "-8", "evidence": L("3 offres écartées pour « trajet »", "3 offers discarded for « commute »")}],
    "rejected": [], "updated_at": iso(1)})
print(f"Données de démonstration écrites dans {data_dir}")
