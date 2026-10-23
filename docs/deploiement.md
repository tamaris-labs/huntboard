# Déploiement de l'application autonome

## Prérequis

- Docker et Docker Compose (v2).
- Une clé d'API de modèle de langage :
  - **Claude** (recommandé) : console Anthropic, clé `sk-ant-…`. La recherche web intégrée
    n'est disponible qu'avec ce fournisseur. Fixez un plafond de dépense dans la console.
  - ou toute API **compatible OpenAI** : OpenAI, Gemini (point d'accès compatible), Mistral,
    ou un modèle local via **Ollama** (`LLM_BASE_URL=http://host.docker.internal:11434/v1`).

## Installation

```bash
git clone https://github.com/tamaris-labs/huntboard.git
cd huntboard
cp .env.example .env
nano .env                   # LLM_API_KEY, APP_PASSWORD, et si souhaité IMAP_* et NOTIFY_URL
docker compose up -d --build
docker compose logs -f      # « Veille planifiée : 30 8 * * 1-5 »
```

L'interface est disponible sur `http://<serveur>:8000` (identifiant libre, mot de passe
`APP_PASSWORD`).

## Lecture des alertes e-mail

1. Créez vos alertes sur LinkedIn (Emplois > Alertes, envoi par e-mail, fréquence
   quotidienne), HelloWork, Michael Page…
2. Gmail : activez la validation en deux étapes, créez un **mot de passe d'application**
   (compte Google > Sécurité), puis renseignez `IMAP_HOST=imap.gmail.com`, `IMAP_USER` et
   `IMAP_PASSWORD`. La boîte est ouverte en lecture seule ; aucun message n'est modifié.
3. Ajoutez d'autres expéditeurs dans `ALERT_SENDERS` si besoin.

## Notification sur téléphone

Installez l'application **ntfy** (Android ou iOS), abonnez-vous à un sujet au nom difficile
à deviner, et renseignez `NOTIFY_URL=https://ntfy.sh/<votre-sujet>`. Le résumé de chaque
passage y est publié.

## Exposition sur Internet

L'application gère une authentification simple ; pour un accès depuis l'extérieur, placez-la
derrière un proxy inverse en HTTPS (Caddy, Traefik, Nginx) et définissez toujours
`APP_PASSWORD`. Exemple Caddy :

```
huntboard.mondomaine.fr {
  reverse_proxy localhost:8000
}
```

## Sauvegarde et mise à jour

```bash
docker compose cp huntboard:/data/huntboard.sqlite3 ./sauvegarde-huntboard.sqlite3   # sauvegarde
git pull && docker compose up -d --build                                  # mise à jour
```

## Coût indicatif

Avec Claude, un passage de veille consomme une quinzaine de recherches web (0,01 $ chacune)
et quelques dizaines de milliers de jetons. Les tâches d'extraction utilisent le modèle
rapide (`LLM_MODEL_QUICK`), la notation et les entretiens le modèle avancé. Réduisez
`WEB_SEARCH_MAX_USES` ou choisissez des modèles plus légers pour limiter la dépense.

## Dépannage

| Symptôme | Piste |
|---|---|
| « Aucun modèle configuré » | `LLM_API_KEY` absente du `.env` ; relancer `docker compose up -d` |
| Aucune offre web avec Ollama ou OpenAI | La recherche web intégrée exige `LLM_PROVIDER=anthropic` ; seules les pages listées dans les sources sont lues |
| Alertes non lues | Vérifier `IMAP_*`, le mot de passe d'application, et `ALERT_SENDERS` |
| Historique des passages | `GET /api/veille/runs` |

## Publication sur GitHub

Dépôt : `tamaris-labs/huntboard`. Deux workflows GitHub Actions (`.github/workflows/`) :

| Workflow | Déclencheur | Rôle |
|---|---|---|
| `ci.yml` | chaque push ou pull request | tests Python, vérification syntaxique de la page et du shim, recherche de données personnelles |
| `release.yml` | tag `v*` (ex. `v2.2.0`), ou lancement manuel depuis l'onglet Actions avec un numéro de version | image Docker publiée sur `ghcr.io/tamaris-labs/huntboard`, release GitHub avec `huntboard-skill.zip` (kit Claude) |

Publier une version :

```bash
git tag v2.2.0 && git push origin v2.2.0
```

Puis, sur le serveur : `docker pull ghcr.io/tamaris-labs/huntboard:latest` (ou `docker compose up -d
--build` depuis le dépôt). Pour le kit Claude, téléchargez `huntboard-skill.zip` depuis la page
Releases et ajoutez-le comme skill dans Claude.

Avant toute publication : `python scripts/check_personal_data.py --history` avec votre propre
fichier `.personal-data-denylist` (nom, adresse, entreprises de vos candidatures, identifiants
d'artefact ou de tâche…), qui n'est jamais versionné.
