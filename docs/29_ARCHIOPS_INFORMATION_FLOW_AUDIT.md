# ARCHI OPS Information Flow Audit

## 1. Architecture réelle observée

```txt
Utilisateur
  ↓
ConversationLoop / cli.py
  ↓
Resource Intake
  ↓
Intent Fusion
  ↓
Coordinator
  ↓
Task Packet Builder
  ↓
Packet metadata + packet content
  ↓
Guidance Renderer / Trace Renderer
  ↓
Utilisateur
```

### Flux observé côté données

```txt
archi_ops/index.yaml
  ↓
load_archi_ops_context()
  ↓
SelectionItem(path, reason, content, lines)
  ↓
build_task_packet()
  ↓
BuiltPacket(metadata, content)
  ↓
ConversationLoop / render_analysis_restitution()
  ↓
message final utilisateur
```

---

## 2. Informations disponibles par étape

| Étape | Informations disponibles |
| ----- | ------------------------ |
| `archi_ops/index.yaml` | Liste structurée des fichiers et maps indexés, avec `path`, `task_types`, `weight`, `reason`, `lines` |
| `archi_ops/index.md` | Sommaire minimal ARCHI OPS + `Negative Context` extrait par parsing simple |
| `Documents/ARCHIOPS/project.yaml` | Contrat projet local: `name`, `root`, `archiops_path`, `status` et quelques champs projet |
| `load_archi_ops_context()` | Sélection déterministe des fichiers et maps compatibles avec le `task_type`, plafonnée par profil (`minimal`, `standard`, `premium`) |
| `build_task_packet()` | Métadonnées de packet, `selected_files`, `selected_maps`, `selection_reasons`, `negative_context`, `project_contract`, `project_yaml_loaded`, `project_contract_injected` |
| `CoordinatorResult` | `resource`, `intent`, `project`, `coherence`, `guard`, `strategy`, `decision`, `trace`, `packet` |
| `CoordinatorTrace` | `intent`, `project`, `strategy`, `provider`, `archiops`, `decision`, `reason`, `intent_trace`, `advisory`, `dry_run`, `live_run`, `provider_called` |
| `ConversationLoop` | Décision d’affichage: expert flow, clarification, draft preview, traces debug, restitution finale |
| `render_analysis_restitution()` | Résumé lisible final: étapes, cartographie, architecture globale, fichiers clés, dépendances, limites, prochaine action |

---

## 3. Informations perdues

| Information | Présente ici | Perdue ici |
| ----------- | ------------ | ---------- |
| Contenu réel des fichiers de cartographie (`repo-map.md`, `runtime-map.md`, `dependency-map.md`, `semantic-index.md`) | Référencés dans `index.yaml` comme chemins sélectionnables | Perdus dès `load_archi_ops_context()` car le chargeur ne lit pas ces fichiers |
| Structure détaillée d’un projet (architecture, composants, dépendances réelles) | Potentiellement décrite dans les maps ARCHI OPS | Perdue avant le `Task Packet` car seules les entrées d’index et quelques chaînes synthétiques passent |
| Raisons fines de sélection de chaque map ou fichier | Partiellement présentes dans `selection_reasons` | Réduites à une forme courte et path-based dans le packet |
| Contexte sémantique complet du projet | Présent dans `project.yaml`, `index.md`, maps ARCHI OPS | Réduit à des champs simples dans `project_contract` et `negative_context` |
| Diagnostic riche exploitable par l’utilisateur | Présent sous forme de `packet.content` et de traces techniques | Perdu au niveau de la restitution si le renderer ne lit que `packet.metadata` |
| Compréhension exhaustive du paquet généré | Présente dans `BuiltPacket.content` | Non exploitée par le flux de restitution final actuel |

---

## 4. Goulot d’étranglement principal

**Point principal: `slypilot/archi_ops_loader.py`**

Pourquoi ce composant est le principal goulot:

1. Il ne charge pas le contenu des maps ARCHI OPS elles-mêmes.
2. Il travaille à partir de `archi_ops/index.yaml` comme registre de sélection.
3. Il transforme la sélection en `SelectionItem(path, reason, content, lines)`, où `content` est une synthèse minimale, pas la substance du fichier.
4. Ce choix fait que les couches suivantes ne reçoivent pas une cartographie sémantique complète, seulement des chemins, des raisons et des métadonnées.

Conséquence:

```txt
ARCHI OPS indexé
↓
sélection de chemins
↓
packet borné
↓
restitution lisible mais générique
```

Le flux n’est pas cassé fonctionnellement. Il est amputé sémantiquement en amont.

---

## 5. Recommandation

Si nous voulons que SlyPilot restitue réellement ce qu’il comprend d’un projet, le composant qui doit évoluer en priorité est:

**`slypilot/archi_ops_loader.py`**

Raison:

- c’est l’endroit où la cartographie devient sélection
- c’est l’endroit où les maps sont réduites à des entrées d’index
- c’est l’endroit où la perte de sémantique commence

### Ce que cela implique architecturalement

La restitution finale ne peut pas raconter davantage que ce que le chargeur a conservé.
Aujourd’hui, le renderer final est un amplificateur de métadonnées, pas un interprète de cartographie complète.

### Hiérarchie réelle du problème

1. **Premier point de perte**: `archi_ops_loader.py`
2. **Second point de perte**: `build_task_packet()` qui agrège et compact
3. **Troisième point de perte**: `render_analysis_restitution()` qui affiche une vue humaine à partir des métadonnées du packet

Donc, si un seul composant doit évoluer en premier, c’est le chargeur ARCHI OPS.

---

## 6. Lecture synthétique

### Où l’information est créée ?

- Dans `archi_ops/index.yaml` pour les règles de sélection
- Dans `Documents/ARCHIOPS/project.yaml` pour le contrat projet
- Dans les maps ARCHI OPS pour la cartographie réelle du projet

### Où elle est transformée ?

- Dans `load_archi_ops_context()` qui transforme un index de chemins en items sélectionnés
- Dans `build_task_packet()` qui transforme la sélection en packet borné

### Où elle disparaît ?

- Dès que `load_archi_ops_context()` ne lit pas les fichiers de cartographie eux-mêmes
- Puis au moment où `render_analysis_restitution()` n’exploite que les métadonnées du packet

### Quel composant est responsable ?

- Principalement `slypilot/archi_ops_loader.py`

### Quel est le prochain chantier prioritaire ?

- Faire évoluer le contrat de chargement ARCHI OPS pour que le chargeur expose une synthèse sémantique exploitable, et pas seulement une sélection de chemins

