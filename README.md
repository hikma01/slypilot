# SlyPilot — Orientation structurante du 2026-11-27

**Statut :** `TRANSVERSE_PILLAR_CANDIDATE / NOT_ACTIVE`. SlyPilot est le **candidat pour le pilier de coordination transverse de SlyAdjoint**. SlyDev est **conservé comme outil spécialisé de développement**, avec sa navigation et ses modules M01–M06 inchangés.

**Point de départ de refondation :** [Contrat V0 et reset logique](docs/44_TRANSVERSE_PILLAR_REFOUNDATION_V0.md) · [RFC SlyMethod de vision](https://github.com/hikma01/slymethod/blob/main/04_Architecture/RFC/RFC-SLYMETHOD-SYSTEME-AGENTIQUE-001.md).

L'historique ci-dessous reste documentaire et **n'est pas une preuve de capacité opérationnelle du nouveau pilier**. Aucun ancien module n'est implicitement admis dans la baseline V0.

---

## Description du SlyPilot historique (LEGACY)

SlyPilot is a deterministic technical coordinator designed to reduce context before sending a task to an AI provider.

## V1 Scope

This repository is intentionally minimal. It establishes:

- a clean Python package layout
- documentation placeholders
- an ARCHI OPS index space
- test scaffolding
- the official Task Packet contract
- schema and example packets

It does not implement business logic, provider adapters, packet building, redaction, storage engines, or complex routing.

## Repository Structure

- `slypilot/`: package skeleton
- `archi_ops/`: knowledge and index placeholders
- `docs/`: project documentation
- `examples/`: official packet examples
- `schemas/`: validation schema drafts
- `tests/`: structure validation and baseline test scaffolding

## Current Status

SlyPilot V1 is stabilized.

Validated pieces:

- deterministic intake and classification
- ARCHI OPS loader and structured index
- task packet builder with guardrails
- single-provider adapter
- simple append-only history
- offline controlled benchmark for packet value

SlyPilot is also the pilot project for validating new SlyMethod execution artifacts before wider rollout.

## Authority

The authoritative registry for autonomous software assets is:

- [SlyGouv/PROJECT_REGISTRY.md](../SlyGouv/PROJECT_REGISTRY.md) v1.0 / `QUALIFIED_BASELINE`

This repository is an operational surface only. It does not redefine the patrimony registry.

## Official Commands

### Tests

```bash
python3 -m unittest discover
```

### Terminal Usage

```bash
slypilot --help
slypilot --dry-run "analyse architecture SlyPilot"
slypilot --live-run "explique problème login Hermes"
```

### Dry Run

```bash
python3 -m slypilot.cli "your request here" --dry-run
```

### Live Run

```bash
python3 -m slypilot.cli "your request here" --live-run
```

## Limits

V1 does not include:

- provider routing
- multi-provider selection
- embeddings
- vector search
- advanced memory
- automatic history-based selection
- agent autonomy
- SQLite-backed persistence

## Next Step

Future phases should only expand the system if there is field evidence that a new capability is required.

For method evolution, SlyPilot serves as the cross-validation project after SlyCV.

## Contract Note

The repository currently stays within documentation-only scope for Task Packet V1. No provider adapter, builder, redactor, storage engine, or routing logic is implemented yet.
