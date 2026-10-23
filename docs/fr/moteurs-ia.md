# Moteurs d'IA et recherche web (application autonome)

*English version: [ai-engines.md](../en/ai-engines.md)*

L'application autonome fonctionne avec Claude (API Anthropic) ou avec toute API **compatible
OpenAI** : OpenAI, Gemini, Mistral, Grok, DeepSeek, OpenRouter, ou un modèle local servi par
Ollama ou LM Studio. La **recherche web**, qui alimente la veille et les suggestions de sources,
se règle à part : recherche intégrée du fournisseur quand elle existe, ou service de recherche
externe (Brave, Tavily, SearXNG) utilisable avec n'importe quel modèle.

Tout se règle dans le fichier `.env` ou, sans redémarrage, dans Réglages › Apprentissage et
données › **Connexions** (bloc « Moteur d'IA » avec un menu *Préréglage* pour l'adresse de
l'API, puis bloc « Recherche web »). Les valeurs saisies dans l'interface priment sur le `.env`.

> Le kit Claude n'est pas concerné : il utilise toujours le compte Claude de la personne.

## 1. Choisir un moteur

| Moteur | `LLM_PROVIDER` | `LLM_BASE_URL` | Recherche web intégrée | Assistant avec outils¹ |
|---|---|---|---|---|
| **Claude** (recommandé) | `anthropic` | *(vide)* | Oui | Oui |
| **OpenAI** | `openai` | *(vide)* ou `https://api.openai.com/v1` | Oui (API Responses) | Oui |
| **Gemini** | `openai` | `https://generativelanguage.googleapis.com/v1beta/openai/` | Oui (ancrage Google Search, API native) | Oui |
| **Grok (xAI)** | `openai` | `https://api.x.ai/v1` | Oui (API Responses) | Oui |
| **OpenRouter** (accès à de nombreux modèles) | `openai` | `https://openrouter.ai/api/v1` | Oui, pour tout modèle (suffixe `:online`, ajouté automatiquement) | Selon le modèle |
| **Mistral** | `openai` | `https://api.mistral.ai/v1` | Non : service externe | Oui |
| **DeepSeek** | `openai` | `https://api.deepseek.com/v1` | Non : service externe | Oui |
| **Ollama** (local) | `openai` | `http://host.docker.internal:11434/v1` | Non : service externe | Selon le modèle |
| **LM Studio** (local) | `openai` | `http://host.docker.internal:1234/v1` | Non : service externe | Selon le modèle |

¹ L'assistant consulte vos données et propose des actions quand le modèle sait appeler des
outils (« function calling »). Sinon, il bascule sur une conversation simple, sans accès aux
données ni propositions.

**Trois modèles** sont demandés, par niveau de difficulté :

| Variable | Usage | Conseil |
|---|---|---|
| `LLM_MODEL_QUICK` | Extraction des alertes, tri, géolocalisation | Petit modèle rapide et peu coûteux |
| `LLM_MODEL_DEFAULT` | Conversation, assistant, recherche web, suggestions | Modèle intermédiaire |
| `LLM_MODEL_COMPLEX` | Notation des offres, préparation d'entretien, lettres | Le meilleur modèle du fournisseur |

Les noms de modèles changent souvent : reprenez ceux affichés dans la console du fournisseur
(ou `ollama list` en local). Un même nom peut servir aux trois niveaux.

## 2. Choisir la recherche web

| `WEB_SEARCH` | Effet |
|---|---|
| `auto` *(défaut)* | Recherche intégrée du fournisseur s'il en a une ; sinon SearXNG si `SEARXNG_URL` est renseigné ; sinon Brave ou Tavily si `SEARCH_API_KEY` l'est (clé `tvly-…` = Tavily) ; sinon aucune. |
| `native` | Recherche intégrée du fournisseur uniquement. |
| `brave` | [Brave Search API](https://brave.com/search/api/) (`SEARCH_API_KEY`), offre gratuite limitée. |
| `tavily` | [Tavily](https://tavily.com) (`SEARCH_API_KEY`), offre gratuite limitée. |
| `searxng` | [SearXNG](https://docs.searxng.org) auto-hébergé (`SEARXNG_URL`) : gratuit, aucune clé, requêtes envoyées depuis votre serveur. |
| `none` | Pas de recherche web : la veille lit seulement les pages des sources et vos alertes e-mail. |

Avec un service externe, le modèle reçoit deux outils, « chercher » et « lire une page », et mène
lui-même la recherche : cela fonctionne avec tout modèle capable d'appeler des outils, local
compris. `WEB_SEARCH_MAX_USES` (15 par défaut) borne le nombre de recherches par passage.

L'écran Connexions affiche le mode **réellement en service** (« En service : openai »,
« searxng », ou « aucune recherche web »). Les alertes e-mail restent lues dans tous les cas.

## 3. Exemples de configuration (`.env`)

**Claude, recherche intégrée** (le plus simple, meilleure qualité) :

```env
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-...
LLM_MODEL_QUICK=claude-haiku-5-5
LLM_MODEL_DEFAULT=claude-sonnet-5-5
LLM_MODEL_COMPLEX=claude-opus-5-5
WEB_SEARCH=auto
```

**OpenAI, recherche intégrée** :

```env
LLM_PROVIDER=openai
LLM_API_KEY=sk-...
LLM_BASE_URL=
LLM_MODEL_QUICK=<petit modèle OpenAI>
LLM_MODEL_DEFAULT=<modèle intermédiaire>
LLM_MODEL_COMPLEX=<meilleur modèle>
WEB_SEARCH=auto
```

**Gemini, ancrage Google Search** :

```env
LLM_PROVIDER=openai
LLM_API_KEY=AIza...
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL_QUICK=<modèle Gemini « flash-lite »>
LLM_MODEL_DEFAULT=<modèle Gemini « flash »>
LLM_MODEL_COMPLEX=<modèle Gemini « pro »>
WEB_SEARCH=auto
```

**OpenRouter, n'importe quel modèle avec recherche web** (la recherche est facturée par
OpenRouter, environ 0,02 $ par requête avec les réglages par défaut) :

```env
LLM_PROVIDER=openai
LLM_API_KEY=sk-or-...
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL_QUICK=<fournisseur/modèle>
LLM_MODEL_DEFAULT=<fournisseur/modèle>
LLM_MODEL_COMPLEX=<fournisseur/modèle>
WEB_SEARCH=auto
```

**Mistral + Brave Search** :

```env
LLM_PROVIDER=openai
LLM_API_KEY=<clé Mistral>
LLM_BASE_URL=https://api.mistral.ai/v1
LLM_MODEL_QUICK=<petit modèle Mistral>
LLM_MODEL_DEFAULT=<modèle intermédiaire>
LLM_MODEL_COMPLEX=<grand modèle>
WEB_SEARCH=brave
SEARCH_API_KEY=BSA...
```

**Entièrement local : Ollama + SearXNG** (aucune donnée ne quitte votre serveur, hormis les
requêtes de recherche anonymes de SearXNG) :

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

Les noms de modèles Ollama ci-dessus sont des exemples : choisissez des modèles qui savent
appeler des outils et tiennent dans la mémoire de la machine (`ollama pull <modèle>`). Sous
Linux, `host.docker.internal` demande la ligne `extra_hosts: ["host.docker.internal:host-gateway"]`
dans le service huntboard (déjà présente dans `deploy/docker-compose.searxng.yml`).

## 4. Ajouter SearXNG à côté de Huntboard

Le dossier `deploy/` contient un fichier Compose prêt à l'emploi :

```bash
mkdir huntboard && cd huntboard
curl -fsSLO https://raw.githubusercontent.com/tamaris-labs/huntboard/main/deploy/docker-compose.searxng.yml
mkdir searxng && curl -fsSL -o searxng/settings.yml https://raw.githubusercontent.com/tamaris-labs/huntboard/main/deploy/searxng/settings.yml
curl -fsSL -o .env https://raw.githubusercontent.com/tamaris-labs/huntboard/main/.env.example
nano .env    # WEB_SEARCH=searxng, SEARXNG_URL=http://searxng:8080, modèle d'IA
nano searxng/settings.yml    # remplacer secret_key par une valeur aléatoire
docker compose -f docker-compose.searxng.yml up -d
```

SearXNG doit accepter le format JSON (`search: formats: [html, json]`, déjà présent dans le
fichier fourni). Il n'est exposé qu'au réseau interne de Docker, pas à Internet.

## 5. Coûts et confidentialité

| Choix | Coût | Données envoyées à l'extérieur |
|---|---|---|
| Claude, OpenAI, Gemini, Grok, Mistral, DeepSeek | Au jeton, plus les recherches web intégrées (facturées à la recherche) | CV, critères, offres et notes nécessaires à chaque tâche |
| OpenRouter | Prix du modèle choisi, plus environ 0,02 $ par recherche web | Idem, via OpenRouter |
| Brave, Tavily | Offre gratuite limitée, puis payant | Les requêtes de recherche seulement |
| Ollama + SearXNG | Gratuit (matériel et électricité) | Aucune, hormis les requêtes de recherche |

Fixez un plafond de dépense chez le fournisseur. Les petits modèles locaux notent et rédigent
moins bien : pour la notation (`LLM_MODEL_COMPLEX`), privilégiez le meilleur modèle disponible.

## 6. Dépannage

- **« Aucune recherche web »** affiché alors qu'un fournisseur est configuré : le fournisseur n'a
  pas de recherche intégrée (Mistral, DeepSeek, local) et aucun service externe n'est renseigné.
- **Erreur 401 ou 403** : clé invalide, ou clé du mauvais fournisseur pour l'adresse saisie.
- **Gemini** : la recherche utilise l'API native de Google avec la même clé ; vérifiez que le
  modèle choisi accepte l'ancrage Google Search.
- **SearXNG renvoie une erreur 403** : le format JSON n'est pas activé dans `settings.yml`.
- **L'assistant répond sans consulter les données** : le modèle ne gère pas les outils ;
  choisissez-en un autre pour `LLM_MODEL_DEFAULT`.
- **Ollama injoignable depuis le conteneur** : vérifiez `host.docker.internal` (voir ci-dessus)
  et qu'Ollama écoute sur toutes les interfaces (`OLLAMA_HOST=0.0.0.0`).
