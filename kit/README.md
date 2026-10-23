# Huntboard — Claude kit

Installs Huntboard **in your Claude account**, with no server and no API key: a page (artifact)
and a daily watch (scheduled task). *Version française ci-dessous.*

## Requirements

- A Claude account with artifacts (with storage), scheduled tasks and skills.
- Optional: a mail connector (Gmail…) so the watch reads your LinkedIn, Indeed and HelloWork alerts.

## Install

1. Download `skills/huntboard` (or `huntboard-skill.zip` from the releases).
2. Import it into your skills from Claude's settings.
3. In a conversation, write: **"Set up my Huntboard"**.

Claude publishes your page; a setup assistant then asks for your language, country, CV,
criteria and sources. Claude finally schedules the daily watch.

---

## Version française

Le kit installe Huntboard **dans votre compte Claude**, sans serveur ni clé d'API.

1. Téléchargez `skills/huntboard` (ou l'archive `huntboard-skill.zip`).
2. Importez-le dans vos skills depuis les paramètres de Claude.
3. Écrivez : **« Installe mon Huntboard »**.

Un assistant de démarrage, dans la page, vous demande langue, pays, CV, critères et sources ;
Claude planifie ensuite la veille quotidienne.

## Données personnelles / Personal data

The kit contains no personal data. Your criteria, CV, offers, notes and interview material live
in **your** artifact, private by default. Do not share its link: anyone invited would see your data.
