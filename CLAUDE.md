# CLAUDE.md — context for evolving Huntboard

Read before changing anything. It gives Claude Code (and contributors) what is needed to modify
the project without breaking it.

## What the project is

A personal job-search board shipped two ways that share one interface:

1. **Claude kit** (`kit/skills/huntboard/`): a skill that publishes the page as a claude.ai
   artifact (capabilities `db`, `sample`, `downloads`, `assets`, and `mcp` for the « Claude Code Remote » `fire_trigger` tool once source checking is enabled) and creates a daily scheduled task.
2. **Self-hosted app** (`app/`): FastAPI + SQLite, watch scheduled by APScheduler, multi-provider
   LLM layer, Docker Compose. Web search is pluggable (`settings.web_search`,
   `settings.web_search_backend`, `llm.web_research_json`): provider-native (Anthropic, OpenAI and
   xAI Responses, OpenRouter `:online`, Gemini grounding) or an external service (Brave, Tavily,
   SearXNG) driven through a `web_search`/`read_page` tool loop that works with any tool-calling
   model. See `docs/en/ai-engines.md` (FR: `docs/fr/moteurs-ia.md`).

## Core principle: one page

`kit/skills/huntboard/template/huntboard.html` is **the** interface.
- In an artifact, it reaches data through `window.claude.use("db")`, the model through
  `window.claude.use("sample")`, file saving through `window.claude.use("downloads")` and stored
  files (original CV, translations, letters) through `window.claude.use("assets")`, served at `/_blob/<id>`.
- In the app, `app/frontend/shim.js` provides exactly that interface over the API
  (`/api/db/...`, `/api/llm/sample`, browser download, `/api/assets` + `/_blob/<id>` stored under `data/assets/`). `main.py` injects the shim.

Settings are four groups (Profile, Documents, Search = criteria/tracks/sources, Learning and data).
Read aloud uses the browser `speechSynthesis` (no network); dictation uses `SpeechRecognition` when
available; geocoding by AI runs only on a button.

Assistant (`asTools()`, `asRules()`): page functions passed to `sample(..., {tools})`. Read tools
(`search_offers`, `get_offer`, `get_overview`, `get_settings`, `get_cv`, `search_notes`,
`list_documents`, `open_view`) run directly; every `propose_*` tool only queues a pending action
(`propose()`), applied after the user validates (button, or « oui » / « non » typed or spoken —
`handleYesNo`). Never add a tool that writes without going through `propose()`. In the app,
`shim.js` runs the tool loop against `/api/llm/step` (`llm.tool_step`, Anthropic or
OpenAI-compatible). Without tool support the assistant falls back to a plain chat.

Setup guide (`openGuide()`, `guideSteps()`): checklist overlay from the header button, opened after
onboarding; banners for demo data (`config.demo`) and missing AI. Reset (`#rs-go`) deletes every
collection except `geo/basemap` and restarts onboarding. App-only features use
`window.huntboardApp` (set by `shim.js`): status, `saveSettings` (AI, IMAP, notify →
`<data>/settings.json`, overrides `.env`, secrets write-only), `testLlm`, `testMail`, `runWatch`. The app also follows recruiter e-mails from headers only
(`veille.follow_up_events`: contact address, contact domain or company name → dated event).

Published repository: `tamaris-labs/huntboard` (project at the root). CI: `.github/workflows/ci.yml`;
release on tag `v*`: `.github/workflows/release.yml` (Docker image `ghcr.io/tamaris-labs/huntboard`,
`huntboard-skill.zip` attached to the GitHub release).

Keep the page compatible with both: only `db.collection(...).onSnapshot/doc/get/set`,
`db.doc(...)`, `sample(input, {signal, onText, modelTier, cache})` and
`downloads.save({filename, data})`, `assets.upload(blob, {type})` / `assets.delete(id)`. Any new capability must be added to the shim and the API.
External scripts load lazily and only from cdnjs (pdf.js, mammoth) — the artifact CSP allows
nothing else.

## Internationalisation

All interface strings live in the `I18N` object (`fr`, `en`) at the top of the page script;
static elements use `data-i18n` / `data-i18n-ph`. Prompts are written in English and ask for
output in the user's language (`outLang()`, `style()`). To add a language: add a key set to
`I18N`, an option in the language selects, and a case in `outLang()` / `style()`.

## Data model (JSON document collections)

| Collection | Document | Content |
|---|---|---|
| `config` | `main` | lang, country, onboarded, archive_days, salary_min_k, home_address, home_lat, home_lon (set by tapping the map), geo, roles, domains, contracts, exclusions, weights, partners, profile, free, sources[], tracks[{id, name, active, in_main, notify, frequency daily/weekly, max_per_run, roles, domains, geo, contracts, pay, exclusions, free, sources[]}] |
| `config` | `learned` | lessons[{text, effect, evidence}], rejected[] |
| `offers` | `company-title` | title, company, location, contract, remote, salary, url, source, score, breakdown{geo,tech,seniority,salary,stability}, tier (match/maybe/far/pending), kind (emploi/associe), track (extra track id, absent = main feed), lat, lon, reasons, blockers, published, found_at, raw_text |
| `notes` | offer id | status (nouvelle/creuser/postule/entretien/offre/non_retenu/ecartee), note, contacts[{name, role, company, email, phone, note, added_at}], pos_tags[], neg_tags[], events[{at,text}], applied_at, interview_at, next_action, next_due, updated_at (legacy `fav` = interest) |
| `postings` | offer id | full posting text kept once an offer is at least « creuser »: offer_id, url, text (≤40k), fetched_at, method (web/email/manual), status (ok/unavailable), attempts |
| `prep` | offer id | sheet, sim_turns[], sim_feedback, debrief_in, debrief, write_<kind> |
| `profile` | `cv` | text, filename, translations{lang:{text}} |
| `coach` | `main` | turns[] (last 30) |
| `coach` | `momentum` | goals{applied, triaged, network}, network{weekKey: n}, wins[{at, text}], active_days[] |
| `geo` | `basemap` | url of the vector basemap (`/_blob/<id>` in the artifact, `/basemap.json` in the app) |
| `geo` | `cache` | home{label, lat, lon, src = config.geo text}, places{normalised location: {label, lat, lon}} — filled by AI geocoding in the page |
| `memos` | `m-…` | text, created_at, source (text/voice/assistant), offer_id, offer_label |
| `sources` | `suggestions` | items[{name, url, note, why, target (main or track id), status unverified/ok/moved/blocked/unreachable/no_url/not_checked, title, checked_at, origin ai/web/watch, created_at}], weak[{name, why}], verify{state requested/running/done, requested_at, done_at, by app/task} — never applied to config without the user ticking them in Sources |
| `documents` | `d-…` | name, filename, kind (cv/cv_tr/letter/other), lang, asset_id, size, content_type, created_at, text (extracted, ≤15k chars — used as style reference for letters), offer_id, offer_label |

Business rules:
- The watch **never** writes to `notes` except: create a "postule" note from an application
  acknowledgement, and append a dated event to `events`. Acknowledgements are recognised from any
  sender (job boards, Workday, SmartRecruiters…: `veille.application_acks`); an unknown offer is
  created with tier `pending`, and pending offers are scored at the next run (`score_pending`).
- Source suggestions: the page suggests from the model's knowledge (`sxSuggest`); web checking is
  `huntboardApp.verifySources` in the app (`veille.verify_and_suggest`, endpoint
  `/api/app/sources/verify`) or, in the kit, `mcp.callTool("Claude Code Remote", "fire_trigger")`
  on the on-demand task `config.source_task_id` (`kit/.../prompts/sources.md`). The Monday watch
  adds one or two checked suggestions. Neither ever edits `config.sources`.
- `non_retenu` (recruiter's refusal) is **not** a preference signal for learning.
- Co-founder searches are the extra track `associes` (legacy `config.partners` and `kind: "associe"` are
  migrated by the page on load; `effTrack()` maps old offers).
- Posting texts are fetched once (≤3 attempts) and never overwritten; LinkedIn is never fetched.
- Every run notifies: news, or a short factual encouragement in the user's language when nothing is new.
- One letter generator (`letterPrompt`) behind two entry points: Documents and Prepare › Writing.
- At most 3 `far` offers per run; explicit criteria always override learned trends.
- LinkedIn is never read directly: e-mail alerts only (see `docs/en/limitations.md`).
- Offers with a `track` stay out of the main feed (unless the track has `in_main`), out of learning
  and out of notifications (unless `notify`).
- Map: two views, an SVG radar around home and a geographic map drawn from a vector basemap
  (`kit/skills/huntboard/assets/basemap.json`: Natural Earth countries + IGN departments, own
  Web-Mercator projection, pan/pinch/zoom). No tile server: the artifact sandbox blocks external images.

## Layout

```
app/backend/huntboard/  main.py · store.py · llm.py · veille.py · sources/{email_imap,web}.py
app/frontend/shim.js
kit/skills/huntboard/   SKILL.md · template/huntboard.html · config.example.json · prompts/veille.md
docs/{fr,en}/  docs/screenshots/{,en/}  scripts/{check_personal_data,demo_data}.py
README.md (EN) · README.fr.md · kit/README.md · kit/README.fr.md
```

## Commands

```bash
cd app/backend && pip install -r requirements.txt pytest && python -m pytest -q
HUNTBOARD_DATA_DIR=./data uvicorn huntboard.main:app --reload   # from app/backend
docker compose up -d --build                                     # from the repo root (source)
# deploy/docker-compose.yml: same service from the published image ghcr.io/tamaris-labs/huntboard
python scripts/check_personal_data.py --history                  # before every publication
```

## Conventions

- French texts in formal register (no « on », no hollow jargon, no self-deprecation); English
  texts plain and professional.
- Colours only through `:root` CSS variables (light and dark themes).
- Usable on a phone (~400 px) with no horizontal page scroll.
- No secrets or personal data in the repo: `.env`, `data/` and `.personal-data-denylist` are ignored.
- Any new logic in `veille.py` or `store.py` comes with a test.
- User documentation exists in **both languages with the same content**: `docs/fr/*.md` and
  `docs/en/*.md` (names: presentation, tutoriel/tutorial, architecture, deploiement/deployment,
  parametrage/settings, sources, limitations, moteurs-ia/ai-engines), `README.md` /
  `README.fr.md`, `kit/README.md` / `kit/README.fr.md`. Any change to one language goes into the
  other in the same commit. French docs use `docs/screenshots/`, English docs
  `docs/screenshots/en/` (English demo data: `HUNTBOARD_DEMO_LANG=en`). `CLAUDE.md` and
  `SKILL.md` stay in English.
