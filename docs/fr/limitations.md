# Limites des plateformes et de l'outil

*English version: [limitations.md](../en/limitations.md)*

Huntboard ne lit que ce qu'il a le droit de lire. Cette page explique pourquoi certaines sources
ne sont accessibles que par alerte e-mail, ce que chaque mode de fonctionnement (kit Claude ou
application autonome) peut et ne peut pas faire, et les choix volontairement écartés.

État constaté en octobre 2026. Les conditions des plateformes changent : vérifiez-les avant de
modifier une source.

## 1. Plateformes d'annonces

| Plateforme | API de recherche d'offres | Lecture directe des pages | Mode retenu dans Huntboard |
|---|---|---|---|
| **LinkedIn** | Aucune API publique de lecture des offres. Les API « Talent » (publication d'offres, Apply Connect, intégrations ATS) sont réservées à des partenaires sous contrat et ne permettent pas de rechercher des offres. | Interdite par les conditions d'utilisation (robots, extensions d'automatisation, collecte). Risque de restriction ou de suppression du compte. | **Alertes e-mail** lues dans la boîte de réception. Jamais de connexion au compte. |
| **Indeed** | L'ancienne API « Publisher » de recherche est arrêtée ; les API partenaires couvrent la publication et les candidatures, pas la recherche. Indeed propose en bêta un **connecteur MCP réservé à Claude** (recherche, détail d'offre, données entreprise) avec connexion à un compte Indeed. | Interdite par les conditions d'utilisation ; pages souvent bloquées aux robots. | Alertes e-mail ; dans le kit Claude, le connecteur Indeed peut compléter la veille s'il est activé. |
| **France Travail** | **API « Offres d'emploi v2 » ouverte** : inscription gratuite sur francetravail.io, authentification OAuth2 (client credentials). 150 résultats par page, 1 150 au plus par requête, environ 10 appels par seconde. | Possible mais inutile : l'API est la bonne voie. | Recherche web ; branchement de l'API prévu (voir § 5). |
| **Adzuna** (agrégateur) | API avec clé gratuite, réservée à la recherche d'emploi personnelle et à la recherche académique ; mention « Adzuna » et lien obligatoires à l'affichage ; usage commercial soumis à licence. | Liens de redirection parfois inexploitables : retrouver l'annonce d'origine. | Recherche web ; API possible pour un usage personnel. |
| **APEC** | Pas d'API publique de recherche d'offres connue. | Pages protégées contre les robots. | Recherche web et alertes e-mail. |
| **Welcome to the Jungle** | Pas d'API publique de recherche d'offres connue (ne pas utiliser les API internes du site). Alertes e-mail inopérantes en octobre 2026. | Lecture des pages publiques, à rythme modéré ; les pages de listes (`/fr/pages/emploi-<métier>-<ville>`) se lisent sans script, la recherche du site non. | Recherche web et pages de listes citées dans la consigne de la source ; une alerte LinkedIn sur le même métier rattrape une partie des offres, que LinkedIn republie. |
| **HelloWork, Cadremploi, Michael Page, cabinets** | Pas d'API publique. | Variable selon le site. | Alertes e-mail et recherche web. |
| **Glassdoor** | Pas d'API publique ouverte. | Pages réservées aux comptes connectés. | Non utilisé, sauf alertes e-mail. |

Conséquences pratiques :
- **Les alertes e-mail sont la source principale** pour LinkedIn, Indeed et les cabinets. Leur
  qualité dépend de leur précision : un intitulé et une zone (ou « télétravail ») par alerte ;
  les alertes trop larges (« informatique, France ») noient les bonnes offres.
- Un e-mail d'alerte ne contient qu'un extrait (intitulé, entreprise, lieu, parfois salaire).
  La note est donc provisoire jusqu'à lecture de l'annonce complète, et les informations
  absentes de l'extrait sont signalées comme « à vérifier ».
- Les liens d'agrégateurs (Adzuna, Jooble, etc.) mènent parfois à une page d'attente ou à une
  offre expirée : Huntboard cherche alors l'annonce d'origine chez l'employeur ou sur LinkedIn.

## 2. Kit Claude (artefact et tâche planifiée)

| Sujet | Limite |
|---|---|
| Page Huntboard | Elle s'exécute dans un environnement isolé : elle ne peut appeler aucun site externe. Seules les bibliothèques de cdnjs (lecture PDF et Word) se chargent. Toute la collecte passe donc par la tâche planifiée. |
| Recherche web de la veille | Elle ne voit que les pages publiques indexées, avec un délai d'indexation de quelques heures à quelques jours. Les pages derrière connexion sont invisibles. |
| Messagerie | Le connecteur Gmail est utilisé en **lecture seule** : jamais d'envoi, de suppression ni de classement. Sans connecteur, les étapes « alertes e-mail » sont retirées de la veille. |
| Quotas | La veille et les fonctions d'IA de la page (analyse de CV, assistant, lettres, carte) consomment les limites d'usage du compte Claude de la personne. |
| Fichiers | Le sélecteur de fichiers est bloqué dans certaines applications mobiles ; l'import se fait alors en envoyant le fichier dans la conversation. Les documents stockés acceptent PDF, texte et images, pas les fichiers Word. |
| Carte | Pas de tuiles cartographiques (ressources externes bloquées) : le fond de carte est un fichier vectoriel embarqué (pays, côtes, départements français), sans routes ni noms de rues. La vue « Radar » donne des distances à vol d'oiseau. Les coordonnées sont fournies par la veille ou estimées par l'IA, donc approximatives à l'échelle de la ville. |
| Dictée vocale | La dictée intégrée utilise la reconnaissance vocale du navigateur (Chrome, Edge, Safari) ; dans une vue qui n'autorise pas le micro, la page propose d'utiliser le micro du clavier du téléphone. La lecture à voix haute fonctionne partout, sans réseau. |
| Accès au web depuis la page | Aucun, y compris pour l'IA appelée par la page : elle ne dispose que des outils de la page (lecture des offres, notes, réglages). Les suggestions de sources viennent donc des connaissances du modèle ; leur vérification sur le web passe par une tâche planifiée dédiée, déclenchée par le connecteur « Claude Code Remote » (autorisation demandée au premier usage). |
| Assistant | Ses actions sont des propositions : rien n'est modifié sans validation. Chaque question consomme plusieurs appels au modèle (consultation des données puis réponse). |
| Notifications | Notification de fin de tâche sur le téléphone ; pas de widget Android ou iOS. |

## 3. Application autonome

| Sujet | Limite |
|---|---|
| Messagerie | Lecture IMAP en lecture seule ; Gmail, Yahoo, iCloud et la plupart des fournisseurs exigent un **mot de passe d'application** (double authentification activée). Outlook, Hotmail et Microsoft 365 n'acceptent généralement plus de mot de passe pour IMAP : transférer les alertes vers une autre boîte. |
| Recherche web | Recherche intégrée du fournisseur avec Claude (10 $ pour 1 000 recherches à ce jour, en plus des jetons), OpenAI, Gemini, Grok ou OpenRouter ; pour Mistral, DeepSeek et les modèles locaux, service externe à configurer (Brave, Tavily ou SearXNG auto-hébergé). Sans recherche web, repli sur une lecture HTTP simple des pages des sources, bien moins complète. Voir [moteurs-ia.md](moteurs-ia.md). |
| Modèles locaux (Ollama, LM Studio) | Recherche web par SearXNG ou un service externe ; assistant avec outils seulement si le modèle sait les appeler ; qualité de notation et de rédaction inférieure aux grands modèles. |
| Coûts | Chaque passage de veille note les offres par lots de 15 ; prévoir quelques centimes à quelques dizaines de centimes par jour selon le volume et le modèle. |
| Sources | Vérification des adresses par le serveur ; recherche de sources sur le web dès qu'une recherche web est disponible (sinon suggestions d'après les connaissances du modèle, adresses testées). |
| Carte | Mêmes principes que dans le kit ; sans clé d'IA, seules les offres pour lesquelles la veille a fourni des coordonnées sont placées. |

## 4. Choix volontairement écartés

- **Aucune connexion automatisée à LinkedIn, Indeed ou APEC** (ni identifiants, ni cookies de
  session, ni extension de navigateur) : contraire aux conditions d'utilisation, et le risque
  porte sur le compte de la personne.
- **Aucune candidature automatique** : chaque candidature reste un acte de la personne.
- **Aucun service tiers de « scraping »** : leur légalité et leur pérennité sont incertaines, et
  ils feraient sortir les critères de recherche vers un intermédiaire.
- **Aucun envoi d'e-mail** depuis l'outil : les relances et remerciements sont rédigés, puis
  copiés par la personne.

## 5. Pistes d'évolution

- Source **France Travail** par l'API officielle (clé gratuite à créer sur francetravail.io).
- Source **Adzuna** par API, pour un usage personnel, avec la mention exigée.
- Kit Claude : utilisation du **connecteur Indeed** dans la veille lorsqu'il est activé.
- Application autonome : fond de carte OpenStreetMap optionnel (hors artefact), en respectant
  la politique d'usage des tuiles.
