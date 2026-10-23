# Huntboard

**Votre recherche d'emploi sur un seul tableau.** Des offres trouvées chaque matin et notées
selon vos propres règles, un suivi des candidatures, les contacts et le texte des annonces
conservés, une carte, un assistant IA qui consulte vos données et propose des actions que vous
validez, l'import et la traduction du CV, les lettres de motivation et la préparation
d'entretien. Interface bilingue (français / anglais), utilisable sur téléphone.

[English](README.md) · **Français**

<p align="center">
  <img src="docs/screenshots/offers-mobile.png" width="200" alt="Offres">
  <img src="docs/screenshots/assistant-mobile.png" width="200" alt="Assistant">
  <img src="docs/screenshots/offer-contacts-mobile.png" width="200" alt="Fiche d'offre, contacts et annonce conservée">
  <img src="docs/screenshots/settings-mobile.png" width="200" alt="Complétude du paramétrage">
</p>
<p align="center"><img src="docs/screenshots/dashboard-desktop.png" width="820" alt="Tableau de bord"></p>

> Les captures utilisent des données de démonstration entièrement fictives (`scripts/demo_data.py`).

## ⚠️ Prérequis : une connexion à une IA

Huntboard est construit autour d'un modèle de langage. **Sans lui, l'application perd
l'essentiel de son intérêt** : ni veille quotidienne, ni notation, ni assistant, ni analyse du
CV, ni lettres, ni préparation d'entretien — il ne reste qu'un suivi manuel.

| Distribution | Ce qu'il faut |
|---|---|
| **Kit Claude** | Un compte Claude dont l'offre permet les artefacts et les tâches planifiées. La page utilise votre usage Claude (l'autorisation est demandée une fois). Un connecteur de messagerie (Gmail) est facultatif mais recommandé pour les alertes e-mail. |
| **Application autonome** | Une clé d'API : **Anthropic** (recommandé), ou toute API compatible OpenAI (OpenAI, Gemini, Grok, Mistral, DeepSeek, OpenRouter), ou un modèle local (Ollama, LM Studio). La recherche web vient du fournisseur quand il en dispose (Claude, OpenAI, Gemini, Grok, OpenRouter) ou de Brave, Tavily ou d'un SearXNG auto-hébergé — une installation entièrement locale fonctionne donc aussi. Voir [Moteurs d'IA et recherche web](docs/fr/moteurs-ia.md). Fixez un plafond de dépense chez votre fournisseur. |

## Ce que fait Huntboard

- **Veille quotidienne** — collecte les offres des sites d'emploi, des pages carrières et de vos
  alertes e-mail (LinkedIn, Indeed, HelloWork… LinkedIn n'est jamais lu directement, voir les
  [limites](docs/fr/limitations.md)), note chacune sur 100 selon vos règles (trajet et jours de
  télétravail, rémunération plancher, postes, domaines) avec un détail visible. Chaque matin :
  une notification avec les nouveautés, ou un court message d'encouragement factuel quand rien
  n'est nouveau.
- **Tri qui apprend** — *Intéressé* / *Écarter* avec un motif en un geste ; les tendances
  apprises sont affichées et révocables.
- **Pistes séparées** — missions freelance, postes à l'international, recherche d'associés…
  chacune avec ses critères, ses sources et son rythme, hors du fil principal sauf décision
  contraire.
- **Suivi** — kanban avec une fiche d'offre : dates, prochaine action, notes, historique,
  **contacts** (e-mail, téléphone), et **texte intégral de l'annonce conservé** dès que l'offre
  mérite d'être creusée. Les accusés de réception de candidature (sites d'annonces, Workday,
  SmartRecruiters…) sont enregistrés automatiquement.
- **Assistant** — posez n'importe quelle question sur vos offres, candidatures, contacts, notes
  ou réglages ; il consulte vos données et **propose des modifications que vous validez** d'un
  appui ou en répondant oui / non, par écrit ou à la voix.
- **Notes** — notes libres, tapées ou dictées, consultables et accessibles à l'assistant.
- **Tableau de bord** — élan de la semaine (objectifs, série de jours actifs, prochain petit
  pas, journal des avancées), chiffres clés, **carte** (fond vectoriel ou radar autour du
  domicile), statistiques.
- **Documents et lettres** — CV originaux et traductions conservés ; générateur de lettre de
  motivation avec sélection de l'offre par recherche, inspiré de vos lettres enregistrées.
- **Entretiens** — fiche, simulation notée, débrief ; lecture à voix haute.
- **Paramétrage assisté** — assistant de démarrage, analyse du CV en critères, jauge de
  complétude avec évaluation par l'IA, sources recommandées pour dix pays, **suggestions de
  sources par l'IA** adaptées au profil et au rendement de chaque source, vérifiées sur le web
  (une suggestion hebdomadaire accompagne la veille du lundi).

## Deux façons de l'utiliser

| | **Kit Claude** (`kit/`) | **Application autonome** (`app/`) |
|---|---|---|
| Fonctionne | Dans votre compte Claude (artefact + tâche planifiée) | Sur votre serveur (Docker) |
| Installation | Importer le skill, puis demander à Claude « Installe mon Huntboard » | `docker compose up -d` |
| IA | Votre abonnement Claude | Votre clé d'API (paiement à l'usage) ou un modèle local |

Les deux partagent **la même page** (`kit/skills/huntboard/template/huntboard.html`).

## Démarrage rapide — application autonome

Avec l'image publiée (sans clonage ni compilation) :

```bash
mkdir huntboard && cd huntboard
curl -fsSLO https://raw.githubusercontent.com/tamaris-labs/huntboard/main/deploy/docker-compose.yml
curl -fsSL -o .env https://raw.githubusercontent.com/tamaris-labs/huntboard/main/.env.example   # puis renseigner au moins LLM_API_KEY et APP_PASSWORD
docker compose up -d
```

Ou depuis le code source : `git clone https://github.com/tamaris-labs/huntboard.git && cd huntboard`,
`cp .env.example .env`, puis `docker compose up -d --build`.

Ouvrez `http://localhost:8000` ; l'assistant de démarrage se lance. Image :
`ghcr.io/tamaris-labs/huntboard` (`latest`, ou un numéro de version). Détails :
[docs/fr/deploiement.md](docs/fr/deploiement.md).

Pour essayer avec des données fictives : `HUNTBOARD_DATA_DIR=./demo-data python scripts/demo_data.py`
(ajoutez `HUNTBOARD_DEMO_LANG=en` pour des données en anglais).

## Démarrage rapide — kit Claude

Téléchargez `huntboard-skill.zip` depuis la page *Releases* du dépôt (ou compressez
`kit/skills/huntboard`), ajoutez-le comme skill dans Claude, puis demandez « Installe mon
Huntboard ». Voir [kit/README.fr.md](kit/README.fr.md).

## Documentation

[Présentation](docs/fr/presentation.md) · [Tutoriel](docs/fr/tutoriel.md) · [Architecture](docs/fr/architecture.md) ·
[Déploiement](docs/fr/deploiement.md) · [Moteurs d'IA et recherche web](docs/fr/moteurs-ia.md) · [Paramétrage](docs/fr/parametrage.md) ·
[Sources par pays](docs/fr/sources.md) · [Limites des plateformes et des API](docs/fr/limitations.md) ·
[Contribuer avec Claude Code](CLAUDE.md) (en anglais) ·
[Toute la documentation, en français et en anglais](docs/README.md)

## Confidentialité

Le dépôt ne contient **aucune donnée personnelle** : la configuration livrée est vierge et les
captures utilisent des données fictives. Vos données restent dans votre artefact Claude ou dans
le volume Docker de votre serveur. L'intégration continue exécute
`scripts/check_personal_data.py` ; lancez-le avec `--history` et votre propre
`.personal-data-denylist` (ignoré par Git) avant toute publication.

## Crédits des données

Carte géographique : frontières des pays issues de [Natural Earth](https://www.naturalearthdata.com/)
(domaine public, via [world-atlas](https://github.com/topojson/world-atlas)) et départements
français issus de [france-geojson](https://github.com/gregoiredavid/france-geojson) (IGN Admin
Express, Licence Ouverte / Etalab).

## Licence

[MIT](LICENSE)
