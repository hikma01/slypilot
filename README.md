# SlyPilot

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

## Next Step

The next phase should define the smallest useful intake and classification boundaries before any provider integration work.

## Contract Note

The repository currently stays within documentation-only scope for Task Packet V1. No provider adapter, builder, redactor, storage engine, or routing logic is implemented yet.
