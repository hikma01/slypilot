# ARCHIOPS Deployment Model

## Décision

ArchiOps reste centralisé dans le dépôt SlyPilot.
Les repos projets ne reçoivent que des artefacts de connaissance et la mémoire projet locale.

## Ce qui est autorisé dans un repo cible

- `Documents/ARCHIOPS/project.yaml`
- `Documents/ARCHIOPS/repo-map.md`
- `Documents/ARCHIOPS/runtime-map.md`
- `Documents/ARCHIOPS/dependency-map.md`
- `Documents/ARCHIOPS/business-map.md`
- `Documents/ARCHIOPS/interpreted-tree.md`
- `Documents/ARCHIOPS/semantic-index.md`
- `.slypilot/project_memory.json`

## Ce qui est interdit

- moteur ArchiOps complet
- workers
- orchestrateur
- microservices
- logique d'analyse embarquée

## Bootstrap

La commande `slypilot init <path>` prépare le projet cible.

Si les cartes n'existent pas encore, le bootstrap génère les artefacts locaux.
Si elles existent déjà, SlyPilot relit les cartes et la mémoire projet.

## Freshness signature

La fraîcheur du projet est calculée à partir de :

- `Documents/ARCHIOPS/*.md`
- `requirements.txt`
- `pyproject.toml`
- `package.json`
- `docker-compose.yml`

Si la signature change, SlyPilot effectue un refresh partiel.

## Flux

```txt
Utilisateur
→ SlyPilot
→ ArchiOps centralisé
→ artefacts locaux
→ ProjectMemory
→ synthèse conversationnelle
```

## But

Éviter la duplication du moteur, garder une cartographie persistante, et continuer l'analyse depuis une mémoire projet enrichie.
