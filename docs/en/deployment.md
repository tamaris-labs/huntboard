# Deploying the self-hosted app

*Version française : [deploiement.md](../fr/deploiement.md)*

## Requirements

- Docker and Docker Compose (v2).
- A language model API key:
  - **Claude** (recommended): Anthropic console, `sk-ant-…` key. Set a spending cap in the
    console.
  - or any **OpenAI-compatible** API: OpenAI, Gemini, Mistral, Grok, DeepSeek, OpenRouter, or
    a local model through **Ollama** or LM Studio. See [ai-engines.md](ai-engines.md).

## Quick install with the published image (recommended)

The image is public at `ghcr.io/tamaris-labs/huntboard`: no GitHub account, no cloning, no
build.

```bash
mkdir huntboard && cd huntboard
curl -fsSLO https://raw.githubusercontent.com/tamaris-labs/huntboard/main/deploy/docker-compose.yml
curl -fsSL -o .env https://raw.githubusercontent.com/tamaris-labs/huntboard/main/.env.example
nano .env                   # LLM_API_KEY, APP_PASSWORD, and if wanted IMAP_* and NOTIFY_URL
docker compose up -d
```

Available versions: `latest` (latest stable release), a specific number (`2.2.0`) to pin the
installation, or a pre-release (`2.3.0-beta.2`), which never replaces `latest`. List: the
repository's *Packages* or *Releases* page.

Update: `docker compose pull && docker compose up -d` (data stays in the `huntboard-data`
volume).

## Trying it in a GitHub Codespace (browser, phone included)

On the repository page: **Code › Codespaces › Create codespace on main**. The environment
installs the app, fills it with fictional data and opens it on port 8000 (*Ports* tab ›
*Open in Browser* if it does not open by itself). Without an AI key, the interface can be fully
browsed but the watch and the assistant do not answer; to enable them, add a Codespaces secret
`LLM_API_KEY`. The published image can also be tried there:
`docker run --rm -p 8001:8000 ghcr.io/tamaris-labs/huntboard:latest`. Stop the Codespace after
use to save the free quota.

## AI engine and web search

Claude (Anthropic API) is recommended, but any OpenAI-compatible API works: OpenAI, Gemini,
Mistral, Grok, DeepSeek, OpenRouter, or a local model (Ollama, LM Studio). Web search is set
separately: the provider's built-in search, or an external service (Brave, Tavily, self-hosted
SearXNG) usable with any model. Engine table, `.env` examples and SearXNG setup:
**[ai-engines.md](ai-engines.md)**.

## Settings from the interface

The AI engine (with an address preset menu), web search, mailbox and notification address can
also be set in the app: Settings › Learning and data › **Connections** (*Test* button for the
model). These values are stored in `settings.json`, in the data folder (mode 600), and take
precedence over the `.env`. Secrets are never sent back to the interface. Protect access with
`APP_PASSWORD` as soon as the app can be reached from the Internet.

To start from scratch: Settings › Learning and data › **Reset** (erases the data, keeps the
connections), or delete the Docker volume (`docker compose down -v`).

## Install from source

```bash
git clone https://github.com/tamaris-labs/huntboard.git
cd huntboard
cp .env.example .env
nano .env                   # LLM_API_KEY, APP_PASSWORD, and if wanted IMAP_* and NOTIFY_URL
docker compose up -d --build
docker compose logs -f      # "Veille planifiée : 30 8 * * 1-5"
```

The interface is available at `http://<server>:8000` (any user name, password
`APP_PASSWORD`).

## Reading e-mail alerts

Any IMAP mailbox works: Gmail, Yahoo, iCloud, Orange, Free, SFR, La Poste, OVH, GMX, Proton
(with Proton Mail Bridge)… The simplest is to set it up in the app (Settings › Learning and
data › Connections), which proposes each provider's server and the link to create an **app
password**. Outlook, Hotmail and Microsoft 365 generally no longer accept passwords for IMAP:
forward your alerts to another mailbox or use the Claude kit with a Microsoft connector.

Access is always **read-only** (no message marked as read, moved or deleted). Three readings are
made at each run:

- **Alerts**: e-mails from the listed senders (LinkedIn, Indeed, HelloWork, Welcome to the
  Jungle, APEC, Cadremploi, Michael Page by default; list editable in Connections or with
  `ALERT_SENDERS`) are analysed to extract offers.
- **Application acknowledgements**: confirmation e-mails, whatever the sender (job boards,
  Workday, SmartRecruiters…), move the offer to "Applied", or create it if it is missing.
- **Application follow-up** (can be turned off: tick box in Connections or
  `MAIL_FOLLOW_UPS=false`): only the headers of recent e-mails are read; a message whose sender
  or subject matches the company or a contact of an open application is added to its history
  ("E-mail received from …: subject").

### Setting it up in the .env file

1. Create your alerts on LinkedIn (Jobs > Alerts, sent by e-mail, daily), HelloWork, Michael
   Page…
2. Gmail: turn on two-step verification, create an **app password** (Google account >
   Security), then fill in `IMAP_HOST=imap.gmail.com`, `IMAP_USER` and `IMAP_PASSWORD`. The
   mailbox is opened read-only; no message is changed.
3. Add other senders to `ALERT_SENDERS` if needed.

## Notification on the phone

Install the **ntfy** app (Android or iOS), subscribe to a topic with a hard-to-guess name, and
set `NOTIFY_URL=https://ntfy.sh/<your-topic>`. The summary of each run is published there.

## Exposing it on the Internet

The app handles simple authentication; for access from outside, put it behind an HTTPS reverse
proxy (Caddy, Traefik, Nginx) and always set `APP_PASSWORD`. Caddy example:

```
huntboard.mydomain.com {
  reverse_proxy localhost:8000
}
```

## Backup and update

```bash
docker compose cp huntboard:/data/huntboard.sqlite3 ./huntboard-backup.sqlite3   # backup
git pull && docker compose up -d --build                                  # update (source)
docker compose pull && docker compose up -d                              # update (published image)
```

## Indicative cost

With Claude, a watch run uses about fifteen web searches ($0.01 each) and a few tens of
thousands of tokens. Extraction tasks use the quick model (`LLM_MODEL_QUICK`), scoring and
interviews the advanced model. Lower `WEB_SEARCH_MAX_USES` or choose lighter models to limit
spending. The other engines and the free, fully local option (Ollama and SearXNG) are compared
in [ai-engines.md](ai-engines.md#5-costs-and-privacy).

## Troubleshooting

| Symptom | Lead |
|---|---|
| "No model configured" | `LLM_API_KEY` missing from the `.env`; run `docker compose up -d` again |
| No offers found on the web | Connections shows "no web search": the engine has none (Mistral, DeepSeek, local); set up Brave, Tavily or SearXNG ([ai-engines.md](ai-engines.md)) |
| Alerts not read | Check `IMAP_*`, the app password, and `ALERT_SENDERS` |
| Run history | `GET /api/veille/runs` |

## Publishing on GitHub

Repository: `tamaris-labs/huntboard`. Two GitHub Actions workflows (`.github/workflows/`):

| Workflow | Trigger | Role |
|---|---|---|
| `ci.yml` | every push or pull request | Python tests, syntax check of the page and the shim, personal data scan |
| `release.yml` | `v*` tag (e.g. `v2.2.0`), or manual run from the Actions tab with a version number | Docker image published to `ghcr.io/tamaris-labs/huntboard`, GitHub release with `huntboard-skill.zip` (Claude kit) |

Publishing a version:

```bash
git tag v2.2.0 && git push origin v2.2.0
```

Then, on the server: `docker pull ghcr.io/tamaris-labs/huntboard:latest` (or
`docker compose up -d --build` from the repository). For the Claude kit, download
`huntboard-skill.zip` from the Releases page and add it as a skill in Claude.

Before any publication: `python scripts/check_personal_data.py --history` with your own
`.personal-data-denylist` file (name, address, companies you applied to, artifact or task
ids…), which is never committed.
