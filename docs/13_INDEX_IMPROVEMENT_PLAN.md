# Index Improvement Plan

Date: 2026-05-31

Scope: improve selection quality by adjusting `archi_ops/index.yaml` only.

## 1. État actuel

### Structure actuelle de l'index

`archi_ops/index.yaml` contient trois projets:

- `slypilot`
- `slyscan`
- `hermes`

Each project currently exposes:

- a small `files` list
- a small `maps` list
- deterministic `weight` ordering
- profile limits enforced by the loader

### Observation issue

The loader is functioning as designed.
The relevance gap comes from the index surface being too document-centric and not operationally specific enough for runtime bugs.

### Measured baseline

From the relevance validation:

- SlyScan bug: `0.25`
- SlyPilot architecture: `0.75`
- Hermes explain: `0.6667`

The current index is acceptable for architecture and explain-style requests.
It is too weak for runtime bug selection.

## 2. Lacunes identifiées

### Fichiers critiques manquants

For SlyScan bug handling, the index lacks references to the runtime chain that actually explains upload failures:

- upload route entrypoint
- upload service
- storage adapter
- validation / schema layer
- job or queue boundary
- database ownership notes

For Hermes login / security cases, the index lacks more explicit security and auth paths:

- auth flow
- session continuity
- password or login contract
- security boundary notes

### Incidents runtime non représentés

The SlyScan section does not reflect incident-oriented runtime memory.
It only exposes broad maps such as:

- `runtime-map.md`
- `dependency-map.md`
- `db-map.md`
- `semantic-index.md`

That is enough to reset a diagnosis, but not enough to preselect the files a human would likely choose for an upload bug.

### Cas login / sécurité sous-documentés

Hermes explain/login is partially covered, but the selection surface lacks a dedicated security/auth emphasis.
The current selection gets overview and README, but not enough security-oriented context.

### Dépendances absentes

The index does not encode the minimum operational dependency chain for the bug class:

- route -> service -> storage -> validator -> DB

Instead it only captures documentation layer references.

### Poids incohérents

Current weights are structurally consistent, but not operationally discriminating enough.

Examples:

- `docs/03_ARCHI_OPS_INDEX.md` is too dominant for SlyScan bug cases.
- `README.md` is useful, but too generic to be a high-priority runtime choice.
- `docs/11_CONTEXT_SELECTION_CONTRACT.md` is useful for architecture work, but not strong enough to improve bug relevance.

## 3. Entrées à ajouter

### SlyScan runtime bug entries

Add entries that represent the human-selected runtime chain.

Recommended files to add to the SlyScan project surface:

- `apps/api/src/routes/upload.mjs`
- `apps/api/src/upload.service.mjs`
- `apps/api/src/storage/storage-adapter.mjs`
- `apps/api/src/validation/upload-validator.mjs`
- `apps/api/src/slyscan-db.mjs`
- `apps/api/src/server.mjs` if the incident touches the endpoint entrypoint

If the actual repository uses other names, the equivalent runtime files should be mapped instead.

### SlyScan incident-oriented maps

Add a compact incident map entry that points to the runtime chain:

- `Documents/ARCHIOPS/runtime-map.md`
- a future `upload-runtime-map.md` or equivalent if the case repeats

### Hermes security entries

Add explicit auth/security files:

- `docs/04_SECURITY.md`
- a dedicated auth flow note if one exists
- a session continuity or login flow map if one exists

### Cross-project support entries

Keep the existing cross-project structural entries, but add only if they help selection:

- `docs/01_ARCHITECTURE.md`
- `docs/03_ARCHI_OPS_INDEX.md`
- `README.md`

## 4. Entrées à modifier

### SlyScan file weights

Reduce the relative dominance of generic structural documents for SlyScan bug cases.

Recommended adjustments:

- lower `docs/03_ARCHI_OPS_INDEX.md` weight for `debug` / `patch`
- lower `docs/01_ARCHITECTURE.md` weight for non-architecture SlyScan tasks
- raise runtime-chain weights for upload-related files

### Hermes weights

Raise the security-oriented file weight for login / explain scenarios.

Recommended adjustments:

- keep `docs/00_PROJECT_OVERVIEW.md` high
- increase `docs/04_SECURITY.md` prominence for `explain` / `architecture` / `debug`
- keep `README.md` as a secondary entrypoint, not the top signal

### SlyPilot architecture weights

SlyPilot architecture selection is already acceptable.
Only minor tuning is needed:

- keep `docs/01_ARCHITECTURE.md` high
- keep `README.md` medium
- keep `docs/03_ARCHI_OPS_INDEX.md` as structural support
- keep `docs/11_CONTEXT_SELECTION_CONTRACT.md` as a contextual supplement

## 5. Entrées à supprimer

### Supprimer ou de-prioriser pour SlyScan bug cases

The following are too generic for the bug case if they dominate selection:

- `docs/03_ARCHI_OPS_INDEX.md`
- `docs/10_ARCHIOPS_INTEGRATION_AUDIT.md`
- `docs/11_CONTEXT_SELECTION_CONTRACT.md`

They should remain available, but not as primary bug selectors.

### Supprimer les faux signaux

Remove any future entries that describe the project theoretically but do not help choose a runtime file.

Examples of bad additions:

- index entries that only restate policy
- duplicate docs without runtime value
- speculative files not yet used in incidents

## 6. Impact attendu sur la sélection

### SlyScan bug target

Current score:

- `0.25`

Target after index refinement:

- `0.80+`

How to get there:

1. Add the runtime chain entries.
2. Give them higher weight than generic structural docs for `debug` / `patch`.
3. Keep profile limits unchanged.
4. Keep the loader unchanged.

### Expected effect

For a bug like `corrige bug upload SlyScan`, the loader should move from:

- one document-centric selection

to:

- a small runtime-oriented selection aligned with the human expectation

Expected selected surface after refinement:

- upload route or entrypoint
- upload service
- storage adapter
- validator
- DB or queue boundary
- minimal supporting maps

### Why this should move the score

The current failure is not selection logic.
It is surface coverage.

When the index includes the right runtime files, the deterministic loader can choose them correctly without any intelligence layer.

## Recommendation

Do not modify the loader.
Do not add scoring.
Do not add embeddings.
Do not add provider integration.

Refine the index into a better representation of real runtime incidents.

That is the smallest valid next step.
