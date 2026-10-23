# Huntboard — overview

*Version française : [presentation.md](../fr/presentation.md)*

Huntboard is a personal job-search dashboard. Every morning it finds the offers that match
your criteria, helps you triage them, track your applications and prepare your interviews,
with an AI assistant that knows your data and acts only with your consent.

The screenshots below use entirely fictional data.

## Why

A senior job search involves a dozen sources, dozens of offers a week, applications to follow
up, contacts, interviews and a lot of writing. Huntboard brings everything together, applies
your rules (commute, remote work, pay, roles, fields) to every offer, and cuts the time spent
triaging so you can spend it on what makes the difference: targeted applications, your
network and preparation.

## Prerequisite: an AI connection

The app relies on a language model for the watch, scoring, the assistant, CV analysis, letters
and interview preparation. **Without an AI connection, only manual application tracking
remains.**

- **Claude kit**: a Claude account whose plan allows artifacts and scheduled tasks. The page
  uses your Claude usage; permission is asked once. The Gmail connector, optional, lets the
  watch read your e-mail alerts (LinkedIn, Indeed, HelloWork…).
- **Self-hosted app**: an Anthropic API key (recommended) or a key for an OpenAI-compatible
  API (OpenAI, Gemini, Grok, Mistral, DeepSeek, OpenRouter), or a local model (Ollama,
  LM Studio). Web search comes from the provider when it has one, or from an external service
  (Brave, Tavily, self-hosted SearXNG): see [ai-engines.md](ai-engines.md).

For a step-by-step start, see the [tutorial](tutorial.md).

## Features

### Offers and daily watch
<img src="../screenshots/en/offers-mobile.png" width="260" align="right" alt="Offers">

- Collected from job boards, careers pages and your e-mail alerts (LinkedIn is never read
  directly: see [limitations.md](limitations.md)).
- Score out of 100 with its breakdown (location, technical fit, seniority, pay, stability) and
  blockers.
- One-tap triage (*Interested* / *Discard* with a reason); learned trends are visible and
  revocable.
- Separate tracks: freelance assignments, international roles, co-founder searches, each with
  its own criteria, sources and frequency, without cluttering the main feed.
- A notification every morning: the news, or a short factual encouragement.

<br clear="right">

### Pipeline, contacts and kept postings
<img src="../screenshots/en/offer-contacts-mobile.png" width="260" align="right" alt="Offer page">

- Application kanban (to explore, applied, interview, offer, not selected).
- Offer page: dates, next action and due date, notes, history, calendar link.
- **Contacts** (name, role, e-mail, phone) added by you or found by the watch in your e-mails
  and in postings.
- **Full posting text kept** as soon as an offer is marked "To explore", even if the posting
  disappears afterwards.
- **Application acknowledgements** (job boards, Workday, SmartRecruiters…) recorded
  automatically: the offer moves to "Applied", or is created if it was missing.

<br clear="right">

### Built-in assistant
<img src="../screenshots/en/assistant-mobile.png" width="260" align="right" alt="Assistant">

- Answers about all your data: offers, applications, contacts, postings, notes, documents, CV,
  settings, weekly goals.
- **Proposes** actions (change a stage, set an interview, add a contact, a note, a source, a
  track, edit a criterion) that you **validate** with a tap or by answering "yes" / "no", in
  writing or by voice.
- Free notes, typed or dictated, which the assistant can find again.
- Answers read aloud.

<br clear="right">

### Dashboard and map
<img src="../screenshots/en/dashboard-desktop.png" width="100%" alt="Dashboard">

- **This week's momentum**: goals (applications, offers triaged, network contacts), streak of
  active days, next small step, progress log, daily brief read aloud.
- **Map** of offers and interviews: a real basemap (countries, coastlines, French
  departments) with zoom and pan, or a radar view centred on home.
- Statistics: stages, watch rhythm, source yield.

<img src="../screenshots/en/map-desktop.png" width="100%" alt="Map">

### Assisted setup
<img src="../screenshots/en/settings-mobile.png" width="260" align="right" alt="Setup">

- Setup assistant: language, country, CV, criteria, recommended sources (ten countries).
- CV analysis that proposes a profile and criteria, to accept field by field.
- **Completeness gauge** for the settings, with the missing items and an AI review of their
  consistency.
- Private home address, which can be placed precisely on the map.
- **Source suggestions** tailored to the profile and to the yield of the current sources,
  checked on the web; one or two new ones every Monday.

<br clear="right">

### Documents, letters and interviews
<img src="../screenshots/en/letters-mobile.png" width="260" align="right" alt="Letters">

- Original and translated CVs kept and downloadable (seven translation languages).
- Cover-letter generator: offer picked by search and filters, language, length, inspired by
  your saved letters.
- Interview preparation: brief, scored mock interview, debrief, follow-up and thank-you
  messages.

<br clear="right">

## Two distributions, one page

| | Claude kit | Self-hosted app |
|---|---|---|
| Runs as | claude.ai artifact + scheduled task | Server (Docker) |
| Install | Import the skill, then ask "Set up my Huntboard" | `docker compose up -d` |
| AI | Your Claude plan | Your API key, or a local model |
| Data | The artifact's private database | Docker volume (SQLite) |

## Privacy

The repository contains no personal data; the shipped configuration is blank. Your data stays
in your artifact or on your server. The mailbox is read-only; the tool sends no e-mail, never
signs in to any of your accounts and never applies on your behalf.

## Known limits

See [limitations.md](limitations.md): closed APIs (LinkedIn, Indeed), voice dictation depending
on the browser, basemap without tiles, AI usage quotas.
