---
name: huntboard
description: Sets up and maintains a personal Huntboard in Claude — a job-search board (scored offers, application pipeline, dashboard, AI coach, CV import and translation, interview preparation) fed by a daily automated watch. Use when someone wants to organise or automate their job search, create their Huntboard or "radar emploi", or change its settings.
---

# Huntboard — installation and settings

This skill gives the person **their own** Huntboard: a page (artifact) with its own database,
and a scheduled task that feeds it every morning. Nothing from anyone else is reused.
Speak to the person in their language (French or English).

Skill files:
- `template/huntboard.html` — the page, published as is (bilingual FR/EN, built-in setup assistant);
- `config.example.json` — blank configuration (structure, default weights and sources);
- `prompts/veille.md` — template of the daily scheduled task.

## 1. Publish the page

1. Read `template/huntboard.html` and publish it with the Artifact tool: title « Huntboard »,
   icon `radar`, capabilities `{"db": {}, "sample": {}, "downloads": {}, "assets": {}}`. Do not edit the page.
2. Upload the basemap for the geographic map: Artifact publish with the new page's `url`,
   `file_path` = `assets/basemap.json`, `asset: true`; then ArtifactData `set` collection `geo`,
   doc_id `basemap`, data `{"url": "/_blob/<asset id>", "asset_id": "<asset id>"}`. Without it the
   map falls back to the Radar view.
3. Write `config.example.json` with ArtifactData: `set` on collection `config`, doc_id `main`
   (set `lang` to the person's language first). Check it with a `get`.
4. Tell the person to open the page: a **setup assistant** starts on first opening (language,
   country, CV import and analysis, criteria, recommended sources for their country). They can
   also answer you in the conversation instead; in that case gather the same items and write
   them into `config/main` yourself (fields below).

Configuration fields: `lang`, `country`, `salary_min_k`, `home_address` (private; `home_lat`/`home_lon` when placed on the map), `geo` (home and commute/remote rules in
plain words), `roles` (one per line), `domains`, `contracts`, `exclusions`, `weights`, `partners`
(empty = no co-founder search), `profile` (150–250 word factual summary), `free`, `sources[]`
({name, url, note, active}), `archive_days`, `onboarded`. The CV, if provided, lives in
`profile/cv` ({text, filename}).

Rules: store nothing sensitive (health, detailed finances, identity numbers); write the profile
only from what the person provided.

## 2. Create the daily watch

1. Once the settings exist (read `config/main`; `onboarded` true or `profile` filled), read
   `prompts/veille.md` and replace `{{ARTIFACT_URL}}`, `{{HOME}}`, `{{ZONE}}` and `{{TRAVEL_TIMES}}`
   (estimate commute times from home to the main employment hubs of the zone). Remove steps 4
   and 5 if no mail connector is available, and say that connecting the mailbox later enables
   reading LinkedIn, Indeed and HelloWork alerts.
2. Create the scheduled task with that text, at the time the person chooses (default 8:30 on
   weekdays, in their time zone), with mobile notification on.
3. Offer to run a first pass right away.

## 3. Wrap up

In a few lines: where the Huntboard is, when the watch runs, how to triage (Interested /
Discard with a reason — this trains the scoring), the Coach tab for open questions about roles
and experience, and the Settings tab (CV, criteria, sources, learning, language, export).

## Importing a file sent in the conversation

Mobile apps can block the file picker inside the page. When the person attaches a CV, an offer
(PDF, Word, screenshot) or an export and asks to import it into their Huntboard:
- **CV**: extract the text faithfully, then `set` collection `profile`, doc_id `cv`
  ({text, filename, updated_at}); tell them to run "Analyse my CV" in Settings. Also keep the
  original file: upload it as an asset (Artifact publish with `url`, `file_path`, `asset: true`)
  and `set` a document in `documents` ({id, name, filename, kind: "cv", lang, asset_id, size,
  content_type, created_at, text}).
- **Cover letter or other document** (PDF, text): upload it the same way, with `kind: "letter"`
  or `"other"` and its extracted `text` (letters serve as style references for new ones).
- **Offer**: create a document in `offers` with `tier: "pending"`, `source: "manual"`, `url`
  if known, `title`, `company` and `raw_text`; the next watch scores it.

## Changing an existing installation

Find the person's Huntboard (artifact list), read `config/main`, apply the requested changes
with `update` and `if_version`. Republish the page only when they ask for the new interface
version (publish `template/huntboard.html` to the same URL; data is kept).
