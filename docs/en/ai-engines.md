# AI engines and web search (self-hosted app)

*Version française : [moteurs-ia.md](../fr/moteurs-ia.md)*

The self-hosted app works with Claude (Anthropic API) or with any **OpenAI-compatible** API:
OpenAI, Gemini, Mistral, Grok, DeepSeek, OpenRouter, or a local model served by Ollama or
LM Studio. **Web search**, which feeds the watch and source suggestions, is set separately:
the provider's built-in search when it has one, or an external search service (Brave, Tavily,
SearXNG) usable with any model.

Everything is set in the `.env` file or, without restarting, in Settings › Learning and data ›
**Connections** ("AI engine" block with a *Preset* menu for the API address, then the
"Web search" block). Values entered in the interface take precedence over the `.env`.

> The Claude kit is not concerned: it always uses the person's Claude account.

## 1. Choosing an engine

| Engine | `LLM_PROVIDER` | `LLM_BASE_URL` | Built-in web search | Assistant with tools¹ |
|---|---|---|---|---|
| **Claude** (recommended) | `anthropic` | *(empty)* | Yes | Yes |
| **OpenAI** | `openai` | *(empty)* or `https://api.openai.com/v1` | Yes (Responses API) | Yes |
| **Gemini** | `openai` | `https://generativelanguage.googleapis.com/v1beta/openai/` | Yes (Google Search grounding, native API) | Yes |
| **Grok (xAI)** | `openai` | `https://api.x.ai/v1` | Yes (Responses API) | Yes |
| **OpenRouter** (access to many models) | `openai` | `https://openrouter.ai/api/v1` | Yes, for any model (`:online` suffix, added automatically) | Depends on the model |
| **Mistral** | `openai` | `https://api.mistral.ai/v1` | No: external service | Yes |
| **DeepSeek** | `openai` | `https://api.deepseek.com/v1` | No: external service | Yes |
| **Ollama** (local) | `openai` | `http://host.docker.internal:11434/v1` | No: external service | Depends on the model |
| **LM Studio** (local) | `openai` | `http://host.docker.internal:1234/v1` | No: external service | Depends on the model |

¹ The assistant looks up your data and proposes actions when the model can call tools
("function calling"). Otherwise, it falls back to a plain conversation, with no access to the
data and no proposals.

**Three models** are requested, by difficulty level:

| Variable | Use | Advice |
|---|---|---|
| `LLM_MODEL_QUICK` | Alert extraction, triage, geocoding | Small, fast and cheap model |
| `LLM_MODEL_DEFAULT` | Conversation, assistant, web search, suggestions | Mid-range model |
| `LLM_MODEL_COMPLEX` | Offer scoring, interview preparation, letters | The provider's best model |

Model names change often: use the ones shown in the provider's console (or `ollama list`
locally). The same name can be used for all three tiers.

## 2. Choosing web search

| `WEB_SEARCH` | Effect |
|---|---|
| `auto` *(default)* | The provider's built-in search if it has one; otherwise SearXNG if `SEARXNG_URL` is set; otherwise Brave or Tavily if `SEARCH_API_KEY` is (a `tvly-…` key means Tavily); otherwise none. |
| `native` | The provider's built-in search only. |
| `brave` | [Brave Search API](https://brave.com/search/api/) (`SEARCH_API_KEY`), limited free tier. |
| `tavily` | [Tavily](https://tavily.com) (`SEARCH_API_KEY`), limited free tier. |
| `searxng` | Self-hosted [SearXNG](https://docs.searxng.org) (`SEARXNG_URL`): free, no key, queries sent from your server. |
| `none` | No web search: the watch only reads the source pages and your e-mail alerts. |

With an external service, the model gets two tools, "search" and "read a page", and runs the
search itself: this works with any model able to call tools, local ones included.
`WEB_SEARCH_MAX_USES` (15 by default) caps the number of searches per run.

The Connections screen shows the mode **actually in use** ("In use: openai", "searxng", or
"no web search"). E-mail alerts are read in every case.

## 3. Configuration examples (`.env`)

**Claude, built-in search** (simplest, best quality):

```env
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-...
LLM_MODEL_QUICK=claude-haiku-5-5
LLM_MODEL_DEFAULT=claude-sonnet-5-5
LLM_MODEL_COMPLEX=claude-opus-5-5
WEB_SEARCH=auto
```

**OpenAI, built-in search**:

```env
LLM_PROVIDER=openai
LLM_API_KEY=sk-...
LLM_BASE_URL=
LLM_MODEL_QUICK=<small OpenAI model>
LLM_MODEL_DEFAULT=<mid-range model>
LLM_MODEL_COMPLEX=<best model>
WEB_SEARCH=auto
```

**Gemini, Google Search grounding**:

```env
LLM_PROVIDER=openai
LLM_API_KEY=AIza...
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL_QUICK=<Gemini "flash-lite" model>
LLM_MODEL_DEFAULT=<Gemini "flash" model>
LLM_MODEL_COMPLEX=<Gemini "pro" model>
WEB_SEARCH=auto
```

**OpenRouter, any model with web search** (search is billed by OpenRouter, about $0.02 per
request with the default settings):

```env
LLM_PROVIDER=openai
LLM_API_KEY=sk-or-...
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL_QUICK=<provider/model>
LLM_MODEL_DEFAULT=<provider/model>
LLM_MODEL_COMPLEX=<provider/model>
WEB_SEARCH=auto
```

**Mistral + Brave Search**:

```env
LLM_PROVIDER=openai
LLM_API_KEY=<Mistral key>
LLM_BASE_URL=https://api.mistral.ai/v1
LLM_MODEL_QUICK=<small Mistral model>
LLM_MODEL_DEFAULT=<mid-range model>
LLM_MODEL_COMPLEX=<large model>
WEB_SEARCH=brave
SEARCH_API_KEY=BSA...
```

**Fully local: Ollama + SearXNG** (no data leaves your server, apart from SearXNG's anonymous
search queries):

```env
LLM_PROVIDER=openai
LLM_API_KEY=
LLM_BASE_URL=http://host.docker.internal:11434/v1
LLM_MODEL_QUICK=qwen3:8b
LLM_MODEL_DEFAULT=qwen3:14b
LLM_MODEL_COMPLEX=qwen3:32b
WEB_SEARCH=searxng
SEARXNG_URL=http://searxng:8080
```

The Ollama model names above are examples: pick models that can call tools and fit in the
machine's memory (`ollama pull <model>`). On Linux, `host.docker.internal` needs the line
`extra_hosts: ["host.docker.internal:host-gateway"]` in the huntboard service (already present
in `deploy/docker-compose.searxng.yml`).

## 4. Adding SearXNG next to Huntboard

The `deploy/` folder contains a ready-to-use Compose file:

```bash
mkdir huntboard && cd huntboard
curl -fsSLO https://raw.githubusercontent.com/tamaris-labs/huntboard/main/deploy/docker-compose.searxng.yml
mkdir searxng && curl -fsSL -o searxng/settings.yml https://raw.githubusercontent.com/tamaris-labs/huntboard/main/deploy/searxng/settings.yml
curl -fsSL -o .env https://raw.githubusercontent.com/tamaris-labs/huntboard/main/.env.example
nano .env    # WEB_SEARCH=searxng, SEARXNG_URL=http://searxng:8080, AI model
nano searxng/settings.yml    # replace secret_key with a random value
docker compose -f docker-compose.searxng.yml up -d
```

SearXNG must accept the JSON format (`search: formats: [html, json]`, already in the provided
file). It is only exposed to Docker's internal network, not to the Internet.

## 5. Costs and privacy

| Choice | Cost | Data sent outside |
|---|---|---|
| Claude, OpenAI, Gemini, Grok, Mistral, DeepSeek | Per token, plus built-in web searches (billed per search) | CV, criteria, offers and notes needed for each task |
| OpenRouter | Price of the chosen model, plus about $0.02 per web search | Same, through OpenRouter |
| Brave, Tavily | Limited free tier, then paid | Search queries only |
| Ollama + SearXNG | Free (hardware and electricity) | None, apart from search queries |

Set a spending cap with the provider. Small local models score and write less well: for
scoring (`LLM_MODEL_COMPLEX`), prefer the best model available.

## 6. Troubleshooting

- **"No web search"** shown although a provider is configured: the provider has no built-in
  search (Mistral, DeepSeek, local) and no external service is set.
- **401 or 403 error**: invalid key, or a key for the wrong provider for the address entered.
- **Gemini**: search uses Google's native API with the same key; check that the chosen model
  supports Google Search grounding.
- **SearXNG returns a 403 error**: the JSON format is not enabled in `settings.yml`.
- **The assistant answers without looking up the data**: the model does not handle tools;
  choose another one for `LLM_MODEL_DEFAULT`.
- **Ollama unreachable from the container**: check `host.docker.internal` (see above) and that
  Ollama listens on all interfaces (`OLLAMA_HOST=0.0.0.0`).
