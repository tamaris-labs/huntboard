# Déploiement de l'application autonome

## Prérequis

- Docker et Docker Compose (v2).
- Une clé d'API de modèle de langage :
  - **Claude** (recommandé) : console Anthropic, clé `sk-ant-…`. La recherche web intégrée
    n'est disponible qu'avec ce fournisseur. Fixez un plafond de dépense dans la console.
  - ou toute API **compatible OpenAI** : OpenAI, Gemini (point d'accès compatible), Mistral,
    ou un modèle local via **Ollama** (`LLM_BASE_URL=http://host.docker.internal:11434/v1`).

## Installation rapide avec l'image publiée (recommandée)

L'image est publique sur `ghcr.io/tamaris-labs/huntboard` : aucun compte GitHub, aucun clonage,
aucune compilation.

```bash
mkdir huntboard && cd huntboard
curl -fsSLO https://raw.githubusercontent.com/tamaris-labs/huntboard/main/deploy/docker-compose.yml
curl -fsSL -o .env https://raw.githubusercontent.com/tamaris-labs/huntboard/main/.env.example
nano .env                   # LLM_API_KEY, APP_PASSWORD, et si souhaité IMAP_* et NOTIFY_URL
docker compose up -d
```

Versions disponibles : `latest` (dernière version stable), un numéro précis (`2.2.0`) pour figer
l'installation, ou une préversion (`2.3.0-beta.2`), qui ne remplace jamais `latest`. Liste :
page *Packages* du dépôt ou *Releases*.

Mise à jour : `docker compose pull && docker compose up -d` (les données restent dans le volume
`huntboard-data`).

## Essai dans un Codespace GitHub (navigateur, téléphone compris)

Sur la page du dépôt : **Code › Codespaces › Create codespace on main**. L'environnement installe
l'application, la remplit de données fictives et l'ouvre sur le port 8000 (onglet *Ports* ›
*Open in Browser* si elle ne s'ouvre pas seule). Sans clé d'IA, l'interface est entièrement
consultable mais la veille et l'assistant ne répondent pas ; pour les activer, ajoutez un secret
Codespaces `LLM_API_KEY`. L'image publiée peut aussi y être testée :
`docker run --rm -p 8001:8000 ghcr.io/tamaris-labs/huntboard:latest`. Arrêtez le Codespace après
usage pour préserver le quota gratuit.

## Réglages depuis l'interface

Le moteur d'IA, la messagerie et l'adresse de notification se règlent aussi dans l'application :
Réglages › Apprentissage et données › **Connexions** (bouton *Tester* pour le modèle). Ces
valeurs sont enregistrées dans `settings.json`, dans le dossier de données (droits 600), et
priment sur le `.env`. Les secrets ne sont jamais renvoyés à l'interface. Protégez l'accès avec
`APP_PASSWORD` dès que l'application est joignable depuis Internet.

Pour repartir de zéro : Réglages › Apprentissage et données › **Réinitialiser** (efface les
données, conserve les connexions), ou supprimer le volume Docker (`docker compose down -v`).

## Installation depuis le code source

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

Toute messagerie compatible IMAP convient : Gmail, Yahoo, iCloud, Orange, Free, SFR, La Poste, OVH,
GMX, Proton (avec Proton Mail Bridge)… Le plus simple est de la régler dans l'application
(Réglages › Apprentissage et données › Connexions), qui propose le serveur de chaque fournisseur
et le lien pour créer un **mot de passe d'application**. Outlook, Hotmail et Microsoft 365
n'acceptent généralement plus de mot de passe pour IMAP : transférez vos alertes vers une autre
boîte ou utilisez le kit Claude avec un connecteur Microsoft.

L'accès est toujours en **lecture seule** (aucun message marqué comme lu, déplacé ou supprimé).
Deux lectures sont faites à chaque passage :

- **Alertes** : les e-mails des expéditeurs listés (LinkedIn, Indeed, HelloWork, Welcome to the
  Jungle, APEC, Cadremploi, Michael Page par défaut ; liste modifiable dans Connexions ou avec
  `ALERT_SENDERS`) sont analysés pour en extraire les offres.
- **Suivi des candidatures** (désactivable : case dans Connexions ou `MAIL_FOLLOW_UPS=false`) : seuls
  les en-têtes des e-mails récents sont lus ; un message dont l'expéditeur ou l'objet correspond
  à l'entreprise ou à un contact d'une candidature en cours est ajouté à son historique
  (« E-mail reçu de … : objet »).

### Réglage par le fichier .env

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
git pull && docker compose up -d --build                                  # mise à jour (code source)
docker compose pull && docker compose up -d                              # mise à jour (image publiée)
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
