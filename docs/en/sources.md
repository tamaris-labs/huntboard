# Job sources by country

*Version française : [sources.md](../fr/sources.md)*

A starting list to build the source configuration. Access conditions change often: the
"Access" column gives the recommended method for the watch, to check during the first run.

**Legend — Access**: *Web* reading of public pages; *Search* web search on the domain;
*Alert* create an e-mail alert on the site and let the watch read it; *API* official API
available; *No* automated reading forbidden or blocked.

## International sources

| Source | Type | Access | Note |
|---|---|---|---|
| LinkedIn Jobs | General | Alert | Never read directly (terms of use) |
| Indeed | Aggregator | Alert | Pages often blocked to robots |
| Glassdoor | Aggregator + reviews | Alert | Also useful for pay and employee reviews |
| Welcome to the Jungle | Startups, tech, consulting | Search + list pages | FR, ES, CZ, SK, US; e-mail alerts not working in October 2026: read the public list pages (`/fr/pages/emploi-<job>-<city>`) |
| Wellfound (formerly AngelList) | Startups | Search | Strong on funded startups |
| Otta | Tech, startups | Alert | UK, Europe, US |
| Remote OK, We Work Remotely, Remotive | Fully remote | Web | Mostly English-speaking |
| Himalayas, Working Nomads | Fully remote | Web | |
| Hacker News "Who is hiring?" | Tech, startups | Web | Monthly thread |
| Ashby, Greenhouse, Lever, Workable | Hosted careers pages | Search | Search `site:jobs.lever.co <keyword>` etc. |
| Malt, Upwork, Freelancer | Freelance assignments | Alert | Malt strong in FR, ES, DE |
| Cofondateur.fr, YC Co-Founder Matching, CoFoundersLab | Co-founder search | Search / account | YC requires an account |

## France

| Source | Type | Access | Note |
|---|---|---|---|
| APEC | Managers | Search + Alert | Essential for managerial roles |
| France Travail | Public, general | API | "Offres d'emploi" API on francetravail.io; check the update date |
| HelloWork | General | Search + Alert | |
| Cadremploi | Managers | Search + Alert | |
| Welcome to the Jungle | Startups, tech | Search + list pages | Partly relayed by LinkedIn: a LinkedIn alert on the same job catches part of the offers |
| Free-Work | IT, permanent and freelance | Web | Region filters in the URL |
| JobTeaser | Graduates | No | Of little use for experienced profiles |
| Choisir le service public, Emploi-Territorial, Place de l'emploi public | Civil service | Web | |
| Michael Page, Robert Walters, Hays, Expectra | Agencies | Search + Alert | Direct reading often refused |
| Specialised tech and engineering agencies | Agencies | Search | Add those you are in touch with |
| French Tech (regional), competitiveness clusters | Ecosystems | Search | E.g. French Tech Aix-Marseille, SCS cluster, Systematic, Minalogic |
| Intelligence Academy | AI job aggregator | Web | Trace back to the original posting |

## Belgium

| Source | Type | Access |
|---|---|---|
| StepStone.be, Jobat, References (Le Soir) | General | Search + Alert |
| Actiris (Brussels), Forem (Wallonia), VDAB (Flanders) | Public services | Web |
| Ictjob.be | IT | Web |

## Switzerland

| Source | Type | Access |
|---|---|---|
| jobs.ch, jobup.ch (French-speaking), JobScout24 | General | Search + Alert |
| job-room.ch | Public service (SECO) | Web |
| swissdevjobs.ch | IT, pay shown | Web |

## Luxembourg

| Source | Type | Access |
|---|---|---|
| Moovijob, jobs.lu, monster.lu | General | Search |
| ADEM (JobBoard) | Public service | Web |

## Canada (Quebec)

| Source | Type | Access |
|---|---|---|
| Jobboom, Jobillico | Quebec | Search |
| Job Bank (Guichet-Emplois) | Federal public service | Web |
| Québec emploi | Provincial public service | Web |
| Indeed.ca, LinkedIn | General | Alert |

## United Kingdom

| Source | Type | Access |
|---|---|---|
| Reed, Totaljobs, CV-Library | General | Search + Alert |
| Find a job (GOV.UK) | Public service | Web |
| Otta, CWJobs, Technojobs | Tech | Alert / Search |
| Guardian Jobs | Managers, public, non-profit | Search |

## Germany

| Source | Type | Access |
|---|---|---|
| StepStone.de, XING, Indeed.de | General | Alert |
| Bundesagentur für Arbeit (Jobbörse) | Public service | API |
| GermanTechJobs, Berlin Startup Jobs | Tech, startups | Web |

## Spain

| Source | Type | Access |
|---|---|---|
| InfoJobs | General (no. 1) | Search + Alert |
| Tecnoempleo | IT | Web |
| Welcome to the Jungle ES, Manfred | Tech | Search |
| SEPE (Empléate) | Public service | Web |

## Netherlands

| Source | Type | Access |
|---|---|---|
| Nationale Vacaturebank, Indeed.nl | General | Search + Alert |
| Werk.nl (UWV) | Public service | Web |
| Undutchables | Non-Dutch-speaking profiles | Search |

## United States

| Source | Type | Access |
|---|---|---|
| Indeed, LinkedIn, ZipRecruiter, Glassdoor | General | Alert |
| Dice, Built In | Tech | Search |
| USAJOBS | Federal | API |
| Wellfound, YC Work at a Startup | Startups | Search / account |

## Recommendations

1. **Three pillars** in each country: the public service (often an API), one or two dominant
   general boards through e-mail alerts, and one niche source tied to your field.
2. **E-mail alerts rather than scraping** for LinkedIn, Indeed, Glassdoor and agencies: more
   reliable, compliant with the terms of use, and readable by the watch.
3. **Careers pages of target companies**: the hidden market of senior roles shows up there
   before job boards; search with `site:` on Lever, Greenhouse, Ashby, Workday.
4. **Local ecosystem** (French Tech, clusters, incubators) for startups and co-founder
   searches.
5. **Measure the yield**: each source shows the offers found and followed; the
   *Suggest sources with AI* button flags low-yield sources. Turn off what produces nothing
   after three weeks.

The reasons for these access modes (closed APIs, terms of use) are detailed in
[limitations.md](limitations.md).
