# Huntboard — présentation

Huntboard est un tableau de bord personnel de recherche d'emploi. Il repère chaque matin les
offres qui correspondent à vos critères, vous aide à les trier, à suivre vos candidatures et à
préparer vos entretiens, avec un assistant IA qui connaît vos données et agit seulement avec
votre accord.

Les captures ci-dessous utilisent des données entièrement fictives.

## Pourquoi

Une recherche d'emploi de cadre mobilise une dizaine de sources, des dizaines d'offres par
semaine, des candidatures à suivre, des contacts, des entretiens et beaucoup d'écrits. Huntboard
rassemble tout au même endroit, applique vos règles (trajet, télétravail, rémunération,
postes, domaines) à chaque offre, et réduit le temps passé à trier pour le reporter sur ce qui
fait la différence : les candidatures ciblées, le réseau et la préparation.

## Prérequis : une connexion à une IA

L'application repose sur un modèle de langage pour la veille, la notation, l'assistant,
l'analyse du CV, les lettres et la préparation d'entretien. **Sans connexion à une IA, il ne
reste qu'un suivi manuel des candidatures.**

- **Kit Claude** : un compte Claude dont l'offre permet les artefacts et les tâches planifiées.
  La page utilise votre usage Claude ; l'autorisation est demandée une fois. Le connecteur
  Gmail, facultatif, permet de lire vos alertes e-mail (LinkedIn, Indeed, HelloWork…).
- **Application autonome** : une clé d'API Anthropic (recommandé : seul fournisseur avec la
  recherche web intégrée) ou d'une API compatible OpenAI (OpenAI, Gemini, Mistral, Ollama en
  local, sans recherche web).

## Les fonctions

### Offres et veille quotidienne
<img src="screenshots/offers-mobile.png" width="260" align="right" alt="Offres">

- Collecte sur les portails, les pages carrières et vos alertes e-mail (LinkedIn n'est jamais
  lu directement : voir [limitations.md](limitations.md)).
- Note sur 100 avec le détail (lieu, technique, séniorité, rémunération, stabilité) et les
  points bloquants.
- Tri en un geste (*Intéressé* / *Écarter* avec motif) ; les tendances apprises sont visibles
  et révocables.
- Pistes séparées : missions freelance, postes à l'international, recherches d'associés, chacune
  avec ses critères, ses sources et sa fréquence, sans encombrer le fil principal.
- Notification chaque matin : les nouveautés, ou un court message d'encouragement factuel.

<br clear="right">

### Suivi, contacts et annonces conservées
<img src="screenshots/offer-contacts-mobile.png" width="260" align="right" alt="Fiche d'offre">

- Kanban des candidatures (à creuser, envoyée, entretien, proposition, non retenue).
- Fiche d'offre : dates, prochaine action et échéance, notes, historique, lien d'agenda.
- **Contacts** (nom, rôle, e-mail, téléphone) ajoutés par vous ou repérés par la veille dans
  vos e-mails et les annonces.
- **Texte intégral de l'annonce conservé** dès qu'une offre passe « À creuser », même si
  l'annonce disparaît ensuite.

<br clear="right">

### Assistant intégré
<img src="screenshots/assistant-mobile.png" width="260" align="right" alt="Assistant">

- Répond sur l'ensemble de vos données : offres, candidatures, contacts, annonces, notes,
  documents, CV, réglages, objectifs de la semaine.
- **Propose** des actions (changer une étape, fixer un entretien, ajouter un contact, une note,
  une source, une piste, modifier un critère) que vous **validez** d'un appui ou en répondant
  « oui » / « non », par écrit ou à la voix.
- Notes libres, tapées ou dictées, que l'assistant sait retrouver.
- Lecture des réponses à voix haute.

<br clear="right">

### Tableau de bord et carte
<img src="screenshots/dashboard-desktop.png" width="100%" alt="Tableau de bord">

- **Élan de la semaine** : objectifs (candidatures, offres triées, contacts réseau), série de
  jours d'activité, prochain petit pas, journal des avancées, point du jour à écouter.
- **Carte** des offres et entretiens : vrai fond de carte (pays, côtes, départements) avec
  zoom et déplacement, ou vue radar centrée sur le domicile.
- Statistiques : étapes, rythme de la veille, rendement des sources.

<img src="screenshots/map-desktop.png" width="100%" alt="Carte">

### Paramétrage assisté
<img src="screenshots/settings-mobile.png" width="260" align="right" alt="Paramétrage">

- Assistant de démarrage : langue, pays, CV, critères, sources recommandées (dix pays).
- Analyse du CV qui propose profil et critères, à valider champ par champ.
- **Jauge de complétude** du paramétrage, avec les éléments manquants et une évaluation de sa
  cohérence par l'IA.
- Adresse du domicile privée, plaçable précisément sur la carte.

<br clear="right">

### Documents, lettres et entretiens
<img src="screenshots/letters-mobile.png" width="260" align="right" alt="Lettres">

- CV originaux et traduits conservés et téléchargeables (sept langues de traduction).
- Générateur de lettre de motivation : sélection de l'offre par recherche et filtres, langue,
  longueur, inspiration de vos lettres enregistrées.
- Préparation d'entretien : fiche, simulation notée, débrief, relance et remerciement.

<br clear="right">

## Deux distributions, une seule page

| | Kit Claude | Application autonome |
|---|---|---|
| Fonctionnement | Artefact claude.ai + tâche planifiée | Serveur (Docker) |
| Installation | Importer le skill, puis demander « Installe mon Huntboard » | `docker compose up -d` |
| IA | Votre abonnement Claude | Votre clé d'API |
| Données | Base privée de l'artefact | Volume Docker (SQLite) |

## Confidentialité

Le dépôt ne contient aucune donnée personnelle ; la configuration livrée est vierge. Vos données
restent dans votre artefact ou sur votre serveur. La messagerie est lue en lecture seule ;
l'outil n'envoie aucun e-mail, ne se connecte à aucun de vos comptes et ne postule jamais à
votre place.

## Limites connues

Voir [limitations.md](limitations.md) : API fermées (LinkedIn, Indeed), dictée vocale selon le
navigateur, fond de carte sans tuiles, quotas d'usage de l'IA.
