# SlyPilot V1 Stabilization

Date: 2026-05-31

## Status

SlyPilot V1 is frozen at the current architecture boundary.

The system has validated:

- deterministic intake and classification
- ARCHI OPS context selection
- task packet generation
- single-provider live-run flow
- task packet guardrails
- simple append-only history
- offline controlled benchmark for packet value

## Frozen architecture

Keep the following stable:

- intake
- classifier
- project resolver
- ARCHI OPS loader
- task packet builder
- DeepSeek adapter
- guardrails
- simple JSONL history

## Official commands

### Tests

```bash
python3 -m unittest discover
```

### Dry run

```bash
python3 -m slypilot.cli "your request here" --dry-run
```

### Live run

```bash
python3 -m slypilot.cli "your request here" --live-run
```

## Validated guarantees

- deterministic selection
- index-driven context reduction
- no embeddings
- no vector search
- no multi-provider routing
- no automatic history-based selection
- no database-backed memory

## Known limits

- provider output quality still depends on the upstream model
- the index must be maintained manually
- offline benchmark proves controlled packet value only
- network availability is required for live runs

## Validation checklist

- [x] repository structure exists
- [x] tests pass with the official command
- [x] task packet contains guardrails
- [x] history remains append-only and simple
- [x] benchmark offline confirms packet value in controlled cases
- [x] V1 avoids advanced memory and routing features

## Out of scope

- provider router
- provider selector
- multi-provider orchestration
- embeddings
- vector search
- advanced memory
- automatic exploitation of history
- agent autonomy
- SQLite
- architecture rewrite

## Closure note

The repository is now in a stable V1 state.
Any future change should preserve the current deterministic boundary unless a new phase explicitly justifies expansion.
