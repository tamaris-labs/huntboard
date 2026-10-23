# Sources d'offres par pays

*English version: [sources.md](../en/sources.md)*

Liste de départ pour composer la configuration des sources. Les conditions d'accès changent
souvent : la colonne « Accès » indique la méthode conseillée pour la veille, à vérifier lors
du premier passage.

**Légende — Accès** : *Web* lecture des pages publiques ; *Recherche* passer par la recherche
web sur le domaine ; *Alerte* créer une alerte e-mail sur le site et la laisser lire par la
veille ; *API* API officielle disponible ; *Non* lecture automatisée interdite ou bloquée.

## Sources internationales

| Source | Type | Accès | Remarque |
|---|---|---|---|
| LinkedIn Jobs | Généraliste | Alerte | Jamais de lecture directe (conditions d'utilisation) |
| Indeed | Agrégateur | Alerte | Pages souvent bloquées aux robots |
| Glassdoor | Agrégateur + avis | Alerte | Utile aussi pour les salaires et avis d'employés |
| Welcome to the Jungle | Startups, tech, conseil | Recherche | FR, ES, CZ, SK, US |
| Wellfound (ex-AngelList) | Startups | Recherche | Fort sur les startups financées |
| Otta | Tech, startups | Alerte | UK, Europe, US |
| Remote OK, We Work Remotely, Remotive | Télétravail total | Web | Majoritairement anglophone |
| Himalayas, Working Nomads | Télétravail total | Web | |
| Hacker News « Who is hiring? » | Tech, startups | Web | Fil mensuel |
| Ashby, Greenhouse, Lever, Workable | Pages carrières hébergées | Recherche | Chercher `site:jobs.lever.co <mot-clé>` etc. |
| Malt, Upwork, Freelancer | Missions freelance | Alerte | Malt fort en FR, ES, DE |
| Cofondateur.fr, YC Co-Founder Matching, CoFoundersLab | Recherche d'associés | Recherche / compte | YC exige un compte |

## France

| Source | Type | Accès | Remarque |
|---|---|---|---|
| APEC | Cadres | Recherche + Alerte | Indispensable pour les postes de cadres |
| France Travail | Généraliste public | API | API « Offres d'emploi » sur francetravail.io ; vérifier la date d'actualisation |
| HelloWork | Généraliste | Recherche + Alerte | |
| Cadremploi | Cadres | Recherche + Alerte | |
| Welcome to the Jungle | Startups, tech | Recherche | |
| Free-Work | IT, CDI et freelance | Web | Filtres par région dans l'URL |
| JobTeaser | Jeunes diplômés | Non | Peu pertinent pour profils expérimentés |
| Choisir le service public, Emploi-Territorial, Place de l'emploi public | Fonction publique | Web | |
| Michael Page, Robert Walters, Hays, Expectra | Cabinets | Recherche + Alerte | Lecture directe souvent refusée |
| Cabinets spécialisés tech et ingénierie | Cabinets | Recherche | Ajouter ceux avec lesquels vous êtes en contact |
| French Tech (régionales), pôles de compétitivité | Écosystèmes | Recherche | Ex. French Tech Aix-Marseille, pôle SCS, Systematic, Minalogic |
| Intelligence Academy | Agrégateur d'offres IA | Web | Remonter à l'annonce d'origine |

## Belgique

| Source | Type | Accès |
|---|---|---|
| StepStone.be, Jobat, References (Le Soir) | Généralistes | Recherche + Alerte |
| Actiris (Bruxelles), Forem (Wallonie), VDAB (Flandre) | Services publics | Web |
| Ictjob.be | IT | Web |

## Suisse

| Source | Type | Accès |
|---|---|---|
| jobs.ch, jobup.ch (Romandie), JobScout24 | Généralistes | Recherche + Alerte |
| job-room.ch | Service public (SECO) | Web |
| swissdevjobs.ch | IT, salaires affichés | Web |

## Luxembourg

| Source | Type | Accès |
|---|---|---|
| Moovijob, jobs.lu, monster.lu | Généralistes | Recherche |
| ADEM (JobBoard) | Service public | Web |

## Canada (Québec)

| Source | Type | Accès |
|---|---|---|
| Jobboom, Jobillico | Québec | Recherche |
| Guichet-Emplois (Job Bank) | Service public fédéral | Web |
| Québec emploi | Service public provincial | Web |
| Indeed.ca, LinkedIn | Généralistes | Alerte |

## Royaume-Uni

| Source | Type | Accès |
|---|---|---|
| Reed, Totaljobs, CV-Library | Généralistes | Recherche + Alerte |
| Find a job (GOV.UK) | Service public | Web |
| Otta, CWJobs, Technojobs | Tech | Alerte / Recherche |
| Guardian Jobs | Cadres, public, associatif | Recherche |

## Allemagne

| Source | Type | Accès |
|---|---|---|
| StepStone.de, XING, Indeed.de | Généralistes | Alerte |
| Bundesagentur für Arbeit (Jobbörse) | Service public | API |
| GermanTechJobs, Berlin Startup Jobs | Tech, startups | Web |

## Espagne

| Source | Type | Accès |
|---|---|---|
| InfoJobs | Généraliste (n° 1) | Recherche + Alerte |
| Tecnoempleo | IT | Web |
| Welcome to the Jungle ES, Manfred | Tech | Recherche |
| SEPE (Empléate) | Service public | Web |

## Pays-Bas

| Source | Type | Accès |
|---|---|---|
| Nationale Vacaturebank, Indeed.nl | Généralistes | Recherche + Alerte |
| Werk.nl (UWV) | Service public | Web |
| Undutchables | Profils non néerlandophones | Recherche |

## États-Unis

| Source | Type | Accès |
|---|---|---|
| Indeed, LinkedIn, ZipRecruiter, Glassdoor | Généralistes | Alerte |
| Dice, Built In | Tech | Recherche |
| USAJOBS | Fédéral | API |
| Wellfound, YC Work at a Startup | Startups | Recherche / compte |

## Recommandations

1. **Trois piliers** dans chaque pays : le service public (souvent une API), un ou deux
   généralistes dominants en alerte e-mail, et une source de niche liée au métier.
2. **Alertes e-mail plutôt que scraping** pour LinkedIn, Indeed, Glassdoor et les cabinets :
   plus fiable, conforme aux conditions d'utilisation, et lisible par la veille.
3. **Pages carrières des entreprises ciblées** : le marché caché des postes seniors y apparaît
   avant les job boards ; chercher via `site:` sur Lever, Greenhouse, Ashby, Workday.
4. **Écosystème local** (French Tech, pôles, incubateurs, clusters) pour les startups et les
   recherches d'associés.
5. **Mesurer le rendement** : chaque source affiche les offres trouvées et suivies ; le bouton
   *Suggérer des sources avec l'IA* signale les sources peu productives. Désactiver ce qui ne
   produit rien après trois semaines.

Les raisons de ces modes d'accès (API fermées, conditions d'utilisation) sont détaillées dans [limitations.md](limitations.md).
