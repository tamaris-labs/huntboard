# Huntboard — kit Claude

[English](README.md) · **Français**

Installe Huntboard **dans votre compte Claude**, sans serveur ni clé d'API : une page (artefact)
et une veille quotidienne (tâche planifiée).

## Prérequis

- Un compte Claude avec les artefacts (avec stockage), les tâches planifiées et les skills.
- Facultatif : un connecteur de messagerie (Gmail…) pour que la veille lise vos alertes
  LinkedIn, Indeed et HelloWork et vos accusés de réception de candidature.

## Installation

1. Téléchargez `skills/huntboard` (ou l'archive `huntboard-skill.zip` depuis les releases).
2. Importez-le dans vos skills depuis les paramètres de Claude.
3. Dans une conversation, écrivez : **« Installe mon Huntboard »**.

Claude publie votre page ; un assistant de démarrage vous demande ensuite langue, pays, CV,
critères et sources. Claude planifie enfin la veille quotidienne et, si vous le souhaitez, la
tâche à la demande qui vérifie sur le web les sources suggérées.

Guide pas à pas : [docs/fr/tutoriel.md](../docs/fr/tutoriel.md).

## Données personnelles

Le kit ne contient aucune donnée personnelle. Vos critères, CV, offres, notes et préparations
d'entretien vivent dans **votre** artefact, privé par défaut. Ne partagez pas son lien : toute
personne invitée verrait vos données.
