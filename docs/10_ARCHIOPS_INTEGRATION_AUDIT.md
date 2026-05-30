# ARCHI OPS Integration Audit

Date: 2026-05-30

Scope: audit de l’intégration ARCHI OPS vers SlyPilot, sans développement métier.

## 1. État actuel

### Documents analysés

SlyPilot local:

- `README.md`
- `archi_ops/README.md`
- `archi_ops/index.md`
- `docs/01_ARCHITECTURE.md`
- `docs/03_ARCHI_OPS_INDEX.md`
- `docs/08_DECISIONS_LOG.md`
- `tests/test_structure.py`

ARCHI OPS partagé:

- `ARCHI-OPS/README.md`
- `ARCHI-OPS/ARCHIOPS.md`
- `ARCHI-OPS/ARCHIOPS_BOOTSTRAP.md`
- `ARCHI-OPS/ARCHIOPS_ACTIVATION.md`
- `ARCHI-OPS/BOUSSOLE.md`
- `ARCHI-OPS/PROJECT_STRUCTURE.md`
- `ARCHI-OPS/STATUS.md`
- `ARCHI-OPS/ARCHIOPS_VALIDATION_LOG.md`

SlyScan-side entrypoint déjà en place:

- `Documents/ARCHIOPS/README.md`
- `Documents/ARCHIOPS/runtime-map.md`
- `Documents/ARCHIOPS/dependency-map.md`
- `Documents/ARCHIOPS/api-map.md`
- `Documents/ARCHIOPS/db-map.md`
- `Documents/ARCHIOPS/docker-map.md`
- `Documents/ARCHIOPS/semantic-index.md`
- `Documents/ARCHIOPS/VALIDATION_LOG.md`

### Ce qui existe déjà

- SlyPilot possède déjà un espace `archi_ops/` local.
- Le dépôt ARCHI OPS partagé possède déjà les documents canoniques de bootstrap, activation, boussole, structure et validation.
- SlyScan a déjà une couche locale d’entrée ARCHI OPS avec maps incident-orientées.
- La logique de réduction de contexte est déjà formulée comme principe, mais pas encore comme loader intégré dans SlyPilot.

### Constats structurants

- ARCHI OPS est déjà suffisamment structuré pour servir de mémoire contextuelle.
- SlyPilot n’a pas besoin de recréer cette structure.
- Le bon point d’intégration n’est pas un framework supplémentaire, mais une interface documentaire et un chargement sélectif.
- La valeur vient surtout de la sélection du bon contexte, pas d’une nouvelle orchestration.

## 2. Éléments réutilisables

### Réutilisables côté ARCHI OPS partagé

- `BOUSSOLE.md` comme filtre de décision.
- `ARCHIOPS_BOOTSTRAP.md` comme séquence d’entrée déterministe.
- `ARCHIOPS_ACTIVATION.md` comme contrat de chargement minimal.
- `PROJECT_STRUCTURE.md` comme cartographie des zones de vérité.
- `STATUS.md` comme indicateur de périmètre actif.
- `ARCHIOPS_VALIDATION_LOG.md` comme trace de preuve et de valeur.

### Réutilisables côté SlyScan

- `Documents/ARCHIOPS/runtime-map.md` pour le reset diagnostic.
- `Documents/ARCHIOPS/dependency-map.md` pour la chaîne minimale de dépendances.
- `Documents/ARCHIOPS/api-map.md` pour les contrats d’intégration.
- `Documents/ARCHIOPS/db-map.md` pour les vérités runtime.
- `Documents/ARCHIOPS/docker-map.md` pour les points de déploiement utiles.
- `Documents/ARCHIOPS/semantic-index.md` pour les boucles répétitives.
- `Documents/ARCHIOPS/VALIDATION_LOG.md` pour capitaliser la preuve.

### Réutilisables côté SlyPilot

- `archi_ops/index.md` comme espace de mémoire locale.
- `docs/03_ARCHI_OPS_INDEX.md` comme document d’introduction.
- `docs/08_DECISIONS_LOG.md` comme journal stratégique.
- `tests/test_structure.py` comme garde-fou sur la présence de la structure.

## 3. Éléments à adapter

### À adapter dans SlyPilot

- Le dossier `archi_ops/` doit rester une interface locale, pas une copie du repo ARCHI OPS.
- L’index doit devenir un vrai sélecteur de contexte, pas seulement une description statique.
- Les docs SlyPilot doivent distinguer clairement:
  - mémoire projet
  - mémoire incident
  - contrat de chargement
  - éléments explicitement hors scope

### À adapter dans la logique de raccordement

- Le chargement doit commencer par le plus petit noyau utile:
  - boussole
  - activation
  - index local
  - maps incident-orientées
- Le semantic index doit être consulté avant toute lecture large.
- `negative_context` doit être traité comme un filtre d’exclusion, pas comme une rubrique narrative.

### À adapter dans la structure documentaire

- Le système documentaire actuel est un peu trop large pour une V1 très simple.
- Plusieurs couches sont déjà utiles, mais une partie du vocabulaire suggère plus de sophistication que nécessaire.
- La V1 doit privilégier un seul chemin de lecture déterministe.

## 4. Éléments à supprimer

### À supprimer du périmètre actif SlyPilot

- Toute duplication du repo ARCHI OPS partagé.
- Toute tentative de transformer SlyPilot en nouveau framework de mémoire ou d’orchestration.
- Toute logique de provider dans l’audit lui-même.
- Toute idée de loader intelligent au sens ML ou heuristique complexe.

### À supprimer conceptuellement

- La tentation de charger tous les documents "au cas où".
- La confusion entre documentation de contexte et runtime.
- La multiplication des couches de mémoire sans preuve terrain.
- Les maps génériques non reliées à des incidents ou à un symptôme utile.

## 5. Proposition ARCHI OPS Loader V1

### Principe

Le loader V1 doit être un sélecteur documentaire déterministe, pas un moteur d’orchestration.

### Entrées

- demande brute
- projet cible
- type de tâche
- signal de répétition
- présence ou non d’un symptôme connu
- index ARCHI OPS local
- maps locales déjà générées
- `negative_context`

### Traitements

1. Identifier le projet.
2. Vérifier si le symptôme correspond à un cas récurrent.
3. Lire d’abord l’index local.
4. Lire ensuite uniquement la ou les maps utiles.
5. Lire les documents canoniques ARCHI OPS partagés uniquement si le besoin le justifie.
6. Exclure explicitement les éléments marqués `negative_context`.
7. Construire un paquet de contexte court, stable et traçable.

### Sorties

- liste courte de fichiers à lire
- liste courte de fichiers à exclure
- contexte structuré minimal
- justification du choix des sources
- trace de sélection pour audit ultérieur

### Ce que le loader V1 ne fait pas

- il ne calcule pas de stratégie provider
- il ne redéfinit pas ARCHI OPS
- il ne construit pas de packet métier complet
- il ne lance pas de routing complexe
- il ne remplace pas le jugement humain

## 6. Risques

### Risques techniques

- surcharger SlyPilot avec une couche de mémoire trop ambitieuse
- dupliquer des documents déjà présents dans ARCHI OPS
- rendre le chargement trop verbeux et perdre le bénéfice de réduction contextuelle
- introduire des divergences entre le repo partagé et l’interface locale

### Risques organisationnels

- faire croire que SlyPilot doit contenir toute la connaissance ARCHI OPS
- confondre audit d’intégration et réécriture de l’écosystème
- repousser la validation terrain au profit d’une architecture plus élégante

### Risques de complexité

- créer une hiérarchie de documents trop lourde pour une V1
- introduire une intelligence de sélection trop tôt
- multiplier les maps sans besoin réel

## 7. Recommandation

### Version simple

Conserver seulement:

- `archi_ops/index.md`
- `docs/03_ARCHI_OPS_INDEX.md`
- `Documents/ARCHIOPS/runtime-map.md`
- `Documents/ARCHIOPS/dependency-map.md`
- `Documents/ARCHIOPS/semantic-index.md`

Cette version est la plus frugale, mais elle peut être trop pauvre si les incidents se répètent.

### Version recommandée

Conserver:

- le contrat ARCHI OPS partagé
- un index local SlyPilot
- les maps locales incident-orientées
- un filtrage explicite par `negative_context`
- une trace de sélection minimale

Cette version est le meilleur compromis entre simplicité et utilité réelle.

### Version à éviter

- copier le repo ARCHI OPS dans SlyPilot
- créer un nouveau framework de mémoire
- mettre une logique heuristique opaque dans le loader
- charger toutes les maps par défaut
- transformer le loader en orchestrateur

## 8. Challenger la structure

### ARCHI OPS est-il trop complexe ?

Oui, potentiellement, si SlyPilot essaie d’en absorber toute la surface.
Non, si SlyPilot n’en consomme qu’un noyau minimal et déterministe.

### Certaines parties sont-elles inutiles ?

Oui:

- les couches non nécessaires au chargement contextuel immédiat
- les documents qui n’aident ni à sélectionner ni à exclure du contexte

### Peut-on simplifier davantage ?

Oui:

- un index
- quelques maps
- un filtre d’exclusion
- une trace de sélection

### Quels éléments apportent réellement de la valeur ?

- le semantic index
- les maps de dépendances et de runtime
- le negative_context
- la validation log
- le chargement court et reproductible

### Quels éléments relèvent de la surarchitecture ?

- les couches qui ne servent qu’à nommer une intention déjà couverte par l’index
- les mécanismes de sélection non validés par incidents réels
- les copies locales de documents canoniques partagés

## 9. Recommandation finale

La meilleure décision V1 est de garder ARCHI OPS comme mémoire structurée, pas comme sous-système autonome.

SlyPilot doit:

- lire peu
- choisir tôt
- exclure explicitement
- tracer le choix
- éviter toute duplication

Le raccordement doit rester documentaire et déterministe.
Tout ce qui ressemble à une orchestration intelligente doit attendre la preuve terrain.
