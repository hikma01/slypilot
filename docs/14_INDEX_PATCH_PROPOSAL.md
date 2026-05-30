# Index Patch Proposal

Date: 2026-05-31

Scope: proposal only. No code changed. No loader changed.

Goal: improve selection relevance by patching `archi_ops/index.yaml` only.

## 1. État actuel

### SlyScan

Current project surface is too document-centric for runtime bugs.

Current high-signal entries:

- `docs/03_ARCHI_OPS_INDEX.md`
- `docs/01_ARCHITECTURE.md`
- `Documents/ARCHIOPS/runtime-map.md`
- `Documents/ARCHIOPS/dependency-map.md`
- `Documents/ARCHIOPS/db-map.md`
- `Documents/ARCHIOPS/semantic-index.md`

Current issue:

- the runtime bug case is still selecting structural docs instead of operational files

### Hermes

Current surface is partially correct for explain cases, but underpowered for login / security / authentication questions.

Current high-signal entries:

- `docs/00_PROJECT_OVERVIEW.md`
- `README.md`
- `docs/04_SECURITY.md`

Current issue:

- security / auth relevance is present but not strong enough

### SlyPilot

Current surface is acceptable for architecture and does not require a major change.

Current high-signal entries:

- `docs/01_ARCHITECTURE.md`
- `README.md`
- `docs/03_ARCHI_OPS_INDEX.md`
- `docs/11_CONTEXT_SELECTION_CONTRACT.md`

## 2. Proposition

### 2.1 SlyScan project entries

#### Before

```yaml
files:
  - path: docs/03_ARCHI_OPS_INDEX.md
    task_types: [architecture, debug, patch, review, docs]
    weight: 85
    lines: 100
    reason: task_relevance=structural
  - path: docs/01_ARCHITECTURE.md
    task_types: [architecture]
    weight: 70
    lines: 100
    reason: task_relevance=critical

maps:
  - path: Documents/ARCHIOPS/runtime-map.md
    task_types: [debug, patch]
    weight: 100
    reason: runtime_reset
  - path: Documents/ARCHIOPS/dependency-map.md
    task_types: [debug, patch, architecture]
    weight: 90
    reason: dependency_chain
  - path: Documents/ARCHIOPS/db-map.md
    task_types: [debug, patch]
    weight: 80
    reason: data_truth
  - path: Documents/ARCHIOPS/semantic-index.md
    task_types: [debug, patch, architecture]
    weight: 70
    reason: repeat_incident_surface
```

#### Après

```yaml
files:
  - path: apps/api/src/routes/upload.mjs
    task_types: [debug, patch]
    weight: 100
    lines: 160
    reason: task_relevance=critical_runtime
  - path: apps/api/src/upload.service.mjs
    task_types: [debug, patch]
    weight: 95
    lines: 220
    reason: task_relevance=service_boundary
  - path: apps/api/src/storage/storage-adapter.mjs
    task_types: [debug, patch]
    weight: 90
    lines: 180
    reason: task_relevance=storage_boundary
  - path: apps/api/src/validation/upload-validator.mjs
    task_types: [debug, patch]
    weight: 88
    lines: 120
    reason: task_relevance=validation_boundary
  - path: apps/api/src/slyscan-db.mjs
    task_types: [debug, patch, architecture]
    weight: 85
    lines: 180
    reason: task_relevance=data_truth
  - path: docs/03_ARCHI_OPS_INDEX.md
    task_types: [architecture, debug, patch, review, docs]
    weight: 45
    lines: 80
    reason: task_relevance=structural_support
  - path: docs/01_ARCHITECTURE.md
    task_types: [architecture]
    weight: 70
    lines: 100
    reason: task_relevance=critical

maps:
  - path: Documents/ARCHIOPS/runtime-map.md
    task_types: [debug, patch]
    weight: 100
    reason: runtime_reset
  - path: Documents/ARCHIOPS/dependency-map.md
    task_types: [debug, patch, architecture]
    weight: 95
    reason: dependency_chain
  - path: Documents/ARCHIOPS/db-map.md
    task_types: [debug, patch]
    weight: 90
    reason: data_truth
  - path: Documents/ARCHIOPS/semantic-index.md
    task_types: [debug, patch, architecture]
    weight: 75
    reason: repeat_incident_surface
```

### 2.2 Hermes project entries

#### Before

```yaml
files:
  - path: docs/00_PROJECT_OVERVIEW.md
    task_types: [explain, docs]
    weight: 90
    lines: 60
    reason: task_relevance=overview
  - path: docs/04_SECURITY.md
    task_types: [architecture, debug, patch, review, docs]
    weight: 85
    lines: 100
    reason: task_relevance=security
  - path: README.md
    task_types: [explain, architecture, docs]
    weight: 70
    lines: 80
    reason: task_relevance=entrypoint

maps:
  - path: archi_ops/index.md
    task_types: [explain, architecture, docs]
    weight: 100
    reason: entrypoint
  - path: docs/11_CONTEXT_SELECTION_CONTRACT.md
    task_types: [explain, architecture, debug, patch, review, docs]
    weight: 80
    reason: contract
```

#### Après

```yaml
files:
  - path: docs/00_PROJECT_OVERVIEW.md
    task_types: [explain, docs]
    weight: 90
    lines: 60
    reason: task_relevance=overview
  - path: docs/04_SECURITY.md
    task_types: [explain, architecture, debug, patch, review, docs]
    weight: 98
    lines: 100
    reason: task_relevance=security_and_auth
  - path: README.md
    task_types: [explain, architecture, docs]
    weight: 70
    lines: 80
    reason: task_relevance=entrypoint

maps:
  - path: archi_ops/index.md
    task_types: [explain, architecture, docs]
    weight: 100
    reason: entrypoint
  - path: docs/11_CONTEXT_SELECTION_CONTRACT.md
    task_types: [explain, architecture, debug, patch, review, docs]
    weight: 80
    reason: contract
```

### 2.3 SlyPilot project entries

#### Before

```yaml
files:
  - path: docs/01_ARCHITECTURE.md
    task_types: [architecture]
    weight: 90
    lines: 120
    reason: task_relevance=critical
  - path: docs/02_TASK_PACKET_STANDARD.md
    task_types: [debug, patch, review, docs]
    weight: 80
    lines: 140
    reason: task_relevance=high
  - path: docs/03_ARCHI_OPS_INDEX.md
    task_types: [architecture, debug, patch, review, docs]
    weight: 70
    lines: 80
    reason: task_relevance=structural
  - path: docs/00_PROJECT_OVERVIEW.md
    task_types: [explain, docs]
    weight: 60
    lines: 60
    reason: task_relevance=overview
  - path: README.md
    task_types: [architecture, docs]
    weight: 50
    lines: 80
    reason: task_relevance=entrypoint
```

#### Après

```yaml
files:
  - path: docs/01_ARCHITECTURE.md
    task_types: [architecture]
    weight: 90
    lines: 120
    reason: task_relevance=critical
  - path: docs/02_TASK_PACKET_STANDARD.md
    task_types: [debug, patch, review, docs]
    weight: 80
    lines: 140
    reason: task_relevance=high
  - path: docs/03_ARCHI_OPS_INDEX.md
    task_types: [architecture, debug, patch, review, docs]
    weight: 70
    lines: 80
    reason: task_relevance=structural
  - path: docs/11_CONTEXT_SELECTION_CONTRACT.md
    task_types: [architecture, debug, patch, review, docs]
    weight: 75
    lines: 80
    reason: task_relevance=contract_support
  - path: docs/10_ARCHIOPS_INTEGRATION_AUDIT.md
    task_types: [architecture, debug, patch, review, docs]
    weight: 65
    lines: 120
    reason: task_relevance=integration_audit
  - path: docs/00_PROJECT_OVERVIEW.md
    task_types: [explain, docs]
    weight: 60
    lines: 60
    reason: task_relevance=overview
  - path: README.md
    task_types: [architecture, docs]
    weight: 50
    lines: 80
    reason: task_relevance=entrypoint
```

## 3. Justification

### SlyScan

Why add runtime files:

- the current bug case needs the operational chain, not more structural docs
- upload incidents usually live in route -> service -> storage -> validator -> DB
- those files are the direct human selection for a bug upload investigation

Why choose those weights:

- `upload.route` / equivalent should win first because it is the entrypoint
- the service boundary should follow because it usually contains the business boundary
- storage and validation follow because they explain the failure class
- `slyscan-db.mjs` stays high because queue and state truth often explain the visible bug

Why adjust map weights:

- runtime map stays first because it resets diagnosis
- dependency map becomes slightly stronger because it helps reconstruct the chain
- db map stays high because runtime failures often converge there
- semantic index stays useful, but should not dominate a direct runtime bug

### Hermes

Why raise `docs/04_SECURITY.md`:

- login and authentication issues are security-adjacent
- the current selection is good for overview, not strong enough for auth
- increasing this weight makes the loader more likely to surface the relevant context

Why keep overview and README:

- they still help anchor the project quickly
- they remain useful, but secondary to security

### SlyPilot

Why add `docs/11_CONTEXT_SELECTION_CONTRACT.md`:

- architecture requests benefit from the contract context
- it improves architecture-case relevance without changing loader logic

Why add `docs/10_ARCHIOPS_INTEGRATION_AUDIT.md`:

- it provides an explicit bridge between SlyPilot and ARCHI OPS
- it is useful as supporting context, not as a primary bug selector

Why keep weights mostly stable:

- SlyPilot architecture already performs well
- no strong evidence justifies a deeper reshuffle

## 4. Cas SlyScan

### Bug Upload

#### Before

Selected by loader:

- `docs/03_ARCHI_OPS_INDEX.md`

Observed precision:

- `0.25`

#### After

Expected loader surface after patch:

- `apps/api/src/routes/upload.mjs`
- `apps/api/src/upload.service.mjs`
- `apps/api/src/storage/storage-adapter.mjs`
- `apps/api/src/validation/upload-validator.mjs`
- `apps/api/src/slyscan-db.mjs`
- `Documents/ARCHIOPS/runtime-map.md`
- `Documents/ARCHIOPS/dependency-map.md`
- `Documents/ARCHIOPS/db-map.md`

### Expected effect

This patch should move the bug case toward the human selection surface.

Target:

- `selection_precision >= 0.80`

Rationale:

- the loader remains deterministic
- the index now contains the runtime chain the human would actually use
- the generic docs no longer dominate the bug class

## 5. Cas Hermes

### Login

Expected effect after patch:

- `docs/04_SECURITY.md` becomes more likely to appear in the selected set

### Sécurité

Expected effect after patch:

- security questions should resolve through the security document first, not the generic overview

### Authentification

Expected effect after patch:

- login/auth questions should stop stopping at the README and overview layer
- the loader should surface security context more consistently

## 6. Impact attendu sur la sélection

### SlyScan bug

- expected precision: from `0.25` to `0.80+`
- expected selected files: runtime route, service, storage, validation, DB
- expected selected maps: runtime map, dependency map, db map

### Hermes login / security

- expected precision: from `0.6667` to around `0.80`
- expected selected files: overview, README, security
- expected selected maps: entrypoint, contract

### SlyPilot architecture

- expected precision remains high
- no major change expected

## Recommendation

Apply the SlyScan runtime additions first.
Apply the Hermes security weight adjustment second.
Keep SlyPilot mostly stable.

This should improve relevance without any change to the loader or any new intelligence layer.
