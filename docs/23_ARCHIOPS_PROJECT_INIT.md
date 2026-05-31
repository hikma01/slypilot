# ARCHI OPS Project Init

Date: 2026-05-31

## Goal

Provide a minimal deterministic `slypilot init` command that can initialize ARCHI OPS in the current repository.

## Command

```bash
slypilot init
```

## Behavior

When run inside a repository, the command must:

1. detect the current working directory
2. create `Documents/ARCHIOPS/`
3. generate bounded cartography files
4. register the project in `slypilot/archi_ops/index.yaml`
5. allow a later contextual dry-run

## Created files

- `Documents/ARCHIOPS/project.yaml`
- `Documents/ARCHIOPS/repo-map.md`
- `Documents/ARCHIOPS/runtime-map.md`
- `Documents/ARCHIOPS/dependency-map.md`
- `Documents/ARCHIOPS/semantic-index.md`

## Constraints

- deterministic
- bounded scan only
- no provider call
- no embeddings
- no vector search
- no deep repo scan

## Scan surface

Allowed:

- top-level files
- `README.md`
- `package.json`
- `pyproject.toml`
- `requirements.txt`
- `docker-compose.yml`
- `src/`
- `app/`
- `apps/`
- `docs/`
- `tests/`
- `routes/`
- `services/`

Excluded:

- `.git`
- `node_modules`
- `.venv`
- `dist`
- `build`
- `.cache`
- `.env`
- secrets
- binaries

## Validation

The command is valid if the current repo gets an ARCHI OPS folder and SlyPilot registers the project in its global index without falling back to another project.
