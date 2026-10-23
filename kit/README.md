# Huntboard — Claude kit

**English** · [Français](README.fr.md)

Installs Huntboard **in your Claude account**, with no server and no API key: a page (artifact)
and a daily watch (scheduled task).

## Requirements

- A Claude account with artifacts (with storage), scheduled tasks and skills.
- Optional: a mail connector (Gmail…) so the watch reads your LinkedIn, Indeed and HelloWork
  alerts and your application acknowledgements.

## Install

1. Download `skills/huntboard` (or `huntboard-skill.zip` from the releases).
2. Import it into your skills from Claude's settings.
3. In a conversation, write: **"Set up my Huntboard"**.

Claude publishes your page; a setup assistant then asks for your language, country, CV,
criteria and sources. Claude finally schedules the daily watch and, if you agree, the
on-demand task that checks suggested sources on the web.

Step-by-step guide: [docs/en/tutorial.md](../docs/en/tutorial.md).

## Personal data

The kit contains no personal data. Your criteria, CV, offers, notes and interview material live
in **your** artifact, private by default. Do not share its link: anyone invited would see your
data.
