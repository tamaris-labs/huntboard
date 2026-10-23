# Platform and tool limits

*Version française : [limitations.md](../fr/limitations.md)*

Huntboard only reads what it is allowed to read. This page explains why some sources are only
reachable through e-mail alerts, what each mode (Claude kit or self-hosted app) can and cannot
do, and the choices deliberately ruled out.

State as observed in October 2026. Platform terms change: check them before changing a source.

## 1. Job platforms

| Platform | Offer search API | Direct page reading | Mode used in Huntboard |
|---|---|---|---|
| **LinkedIn** | No public API for reading offers. The "Talent" APIs (job posting, Apply Connect, ATS integrations) are reserved for contracted partners and do not allow searching offers. | Forbidden by the terms of use (robots, automation extensions, data collection). Risk of account restriction or deletion. | **E-mail alerts** read in the inbox. Never any sign-in to the account. |
| **Indeed** | The former "Publisher" search API is discontinued; partner APIs cover job posting and applications, not search. Indeed offers in beta an **MCP connector reserved for Claude** (search, job details, company data) with sign-in to an Indeed account. | Forbidden by the terms of use; pages often blocked to robots. | E-mail alerts; in the Claude kit, the Indeed connector can complement the watch if enabled. |
| **France Travail** | **Open "Offres d'emploi v2" API**: free registration on francetravail.io, OAuth2 authentication (client credentials). 150 results per page, at most 1,150 per query, about 10 calls per second. | Possible but pointless: the API is the right way. | Web search; API connection planned (see § 5). |
| **Adzuna** (aggregator) | API with a free key, reserved for personal job search and academic research; "Adzuna" mention and link required when displayed; commercial use requires a licence. | Redirect links sometimes unusable: find the original posting. | Web search; API possible for personal use. |
| **APEC** | No known public offer search API. | Pages protected against robots. | Web search and e-mail alerts. |
| **Welcome to the Jungle** | No known public offer search API (do not use the site's internal APIs). | Reading of public pages, at a moderate pace. | Web search. |
| **HelloWork, Cadremploi, Michael Page, agencies** | No public API. | Varies by site. | E-mail alerts and web search. |
| **Glassdoor** | No open public API. | Pages reserved for signed-in accounts. | Not used, except through e-mail alerts. |

Practical consequences:
- **E-mail alerts are the main source** for LinkedIn, Indeed and agencies. Their quality
  depends on their precision: one title and one area (or "remote") per alert; overly broad
  alerts ("IT, France") drown the good offers.
- An alert e-mail only contains an excerpt (title, company, location, sometimes pay). The score
  is therefore provisional until the full posting is read, and information missing from the
  excerpt is flagged "to check".
- Aggregator links (Adzuna, Jooble, etc.) sometimes lead to a waiting page or an expired offer:
  Huntboard then looks for the original posting at the employer or on LinkedIn.

## 2. Claude kit (artifact and scheduled task)

| Topic | Limit |
|---|---|
| Huntboard page | It runs in an isolated environment: it cannot call any external site. Only cdnjs libraries (PDF and Word reading) load. All collection therefore goes through the scheduled task. |
| Watch web search | It only sees indexed public pages, with an indexing delay of a few hours to a few days. Pages behind a sign-in are invisible. |
| Mailbox | The Gmail connector is used **read-only**: never any sending, deletion or labelling. Without a connector, the "e-mail alerts" steps are removed from the watch. |
| Quotas | The watch and the page's AI features (CV analysis, assistant, letters, map) use the person's Claude account usage limits. |
| Files | The file picker is blocked in some mobile apps; import then works by sending the file in the conversation. Stored documents accept PDF, text and images, not Word files. |
| Map | No map tiles (external resources are blocked): the basemap is an embedded vector file (countries, coastlines, French departments), with no roads or street names. The "Radar" view gives straight-line distances. Coordinates come from the watch or are estimated by the AI, so they are approximate at city level. |
| Voice dictation | Built-in dictation uses the browser's speech recognition (Chrome, Edge, Safari); in a view that does not allow the microphone, the page suggests using the phone keyboard's microphone. Reading aloud works everywhere, offline. |
| Web access from the page | None, including for the AI called by the page: it only has the page's tools (reading offers, notes, settings). Source suggestions therefore come from the model's knowledge; checking them on the web goes through a dedicated scheduled task, fired by the "Claude Code Remote" connector (permission asked on first use). |
| Assistant | Its actions are proposals: nothing changes without validation. Each question uses several model calls (looking up the data, then answering). |
| Notifications | End-of-task notification on the phone; no Android or iOS widget. |

## 3. Self-hosted app

| Topic | Limit |
|---|---|
| Mailbox | Read-only IMAP; Gmail, Yahoo, iCloud and most providers require an **app password** (two-step verification enabled). Outlook, Hotmail and Microsoft 365 generally no longer accept passwords for IMAP: forward the alerts to another mailbox. |
| Web search | Built-in provider search with Claude ($10 per 1,000 searches at the time of writing, on top of tokens), OpenAI, Gemini, Grok or OpenRouter; for Mistral, DeepSeek and local models, an external service to configure (Brave, Tavily or self-hosted SearXNG). Without web search, fallback to simple HTTP reading of the source pages, far less complete. See [ai-engines.md](ai-engines.md). |
| Local models (Ollama, LM Studio) | Web search through SearXNG or an external service; assistant with tools only if the model can call them; scoring and writing quality below the large models. |
| Costs | Each watch run scores offers in batches of 15; expect a few cents to a few tens of cents a day depending on volume and model. |
| Sources | Addresses checked by the server; sources searched on the web whenever web search is available (otherwise suggestions from the model's knowledge, addresses tested). |
| Map | Same principles as in the kit; without an AI key, only offers for which the watch provided coordinates are placed. |

## 4. Choices deliberately ruled out

- **No automated sign-in to LinkedIn, Indeed or APEC** (no credentials, session cookies or
  browser extension): contrary to the terms of use, and the risk falls on the person's account.
- **No automatic applications**: each application remains the person's own act.
- **No third-party "scraping" services**: their legality and durability are uncertain, and they
  would send the search criteria to an intermediary.
- **No e-mail sent** from the tool: follow-ups and thank-you messages are drafted, then copied
  by the person.

## 5. Possible next steps

- **France Travail** source through the official API (free key to create on francetravail.io).
- **Adzuna** source through its API, for personal use, with the required mention.
- Claude kit: use of the **Indeed connector** in the watch when enabled.
- Self-hosted app: optional OpenStreetMap basemap (outside the artifact), respecting the tile
  usage policy.
