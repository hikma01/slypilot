# ARCHIOPS Loader V2

## Vérification des maps

Audit réalisé sur les artefacts présents dans un projet ARCHIOPS préparé.

### Vérification observée sur `SlyAudit`

- `Documents/ARCHIOPS/project.yaml` existe
- `Documents/ARCHIOPS/project.yaml` contient un contrat projet non vide
- `Documents/ARCHIOPS/repo-map.md` existe
- `Documents/ARCHIOPS/repo-map.md` contient une description de structure non vide
- `Documents/ARCHIOPS/runtime-map.md` existe
- `Documents/ARCHIOPS/runtime-map.md` contient des runtimes et des points d’entrée
- `Documents/ARCHIOPS/dependency-map.md` existe
- `Documents/ARCHIOPS/dependency-map.md` contient des dépendances et une note
- `Documents/ARCHIOPS/semantic-index.md` existe
- `Documents/ARCHIOPS/semantic-index.md` contient un index sémantique non vide

## Design du Knowledge Contract

Contrat produit par le loader:

```python
KnowledgeContract(
    project=...,
    repo_map=...,
    runtime_map=...,
    dependency_map=...,
    semantic_index=...,
    important_files=...,
    selection_reason=...,
)
```

Le contrat transporte le contenu brut des maps, sans résumé, sans parsing métier, sans vectorisation.

## Modifications effectuées

- le loader lit maintenant le contenu brut des maps ARCHIOPS depuis le répertoire du projet courant
- le loader expose un `KnowledgeContract`
- `build_task_packet()` transmet ce contrat dans les métadonnées du packet
- la restitution finale peut afficher le contenu transporté

## Tests ajoutés

- vérification de chargement du contrat brut
- vérification du contenu non vide des maps
- vérification de la compatibilité avec le packet builder

## Exemple de contrat produit

```python
KnowledgeContract(
    project="slyaudit",
    repo_map=KnowledgeArtifact(
        path="Documents/ARCHIOPS/repo-map.md",
        content="# REPO MAP\\n...",
        reason="entrypoint",
        exists=True,
        size=221,
    ),
    runtime_map=KnowledgeArtifact(
        path="Documents/ARCHIOPS/runtime-map.md",
        content="# RUNTIME MAP\\n...",
        reason="runtime_reset",
        exists=True,
        size=102,
    ),
    dependency_map=KnowledgeArtifact(
        path="Documents/ARCHIOPS/dependency-map.md",
        content="# DEPENDENCY MAP\\n...",
        reason="dependency_chain",
        exists=True,
        size=157,
    ),
    semantic_index=KnowledgeArtifact(
        path="Documents/ARCHIOPS/semantic-index.md",
        content="# SEMANTIC INDEX\\n...",
        reason="repeat_incident_surface",
        exists=True,
        size=201,
    ),
    important_files=[],
    selection_reason="deterministic_loader",
)
```

