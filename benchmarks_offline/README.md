# Benchmark Offline Controlled

This folder contains the Phase 8.1 offline benchmark for SlyPilot.

## Goal

Compare:

- direct prompt -> mock provider
- prompt -> SlyPilot -> task packet -> mock provider

This benchmark is intentionally offline:

- no DNS
- no external API
- no provider secrets
- no routing
- no scoring automation

## Structure

- `prompts/` fixed benchmark prompts
- `packets/` captured SlyPilot task packets or packet excerpts
- `direct/` direct-mode mock captures
- `slypilot/` SlyPilot-mode mock captures
- `evaluations/` manual comparison sheets and summary

## Fixed cases

- `01_architecture`
- `02_bug_login`
- `03_bug_upload`

## Reproducibility rule

Use the exact same prompts in both modes.
Keep the mock provider output deterministic.
Do not modify loader, index, task packet, or adapter logic for this benchmark.

## Status

Protocol and artifact structure are defined here. The benchmark can be executed and evaluated without network access.
