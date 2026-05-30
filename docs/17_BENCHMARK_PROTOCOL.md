# Benchmark Protocol

Date: 2026-05-31

Purpose: capture comparable outputs for direct-provider runs versus SlyPilot-assisted runs on the same prompts.

## Scope

This protocol defines only the capture format and execution rules for a reproducible benchmark.

It does not modify:

- loader
- index
- task packet
- adapter
- classifier
- project resolver

## Cases

Run the following prompts exactly as written:

1. `analyse architecture SlyPilot`
2. `explique problème login Hermes`
3. `corrige bug upload SlyScan`
4. `audit sécurité Hermes`

## Modes

### Direct provider

Run the prompt directly against the provider with no SlyPilot preprocessing.

Capture the raw provider answer.

### SlyPilot

Run the same prompt through the full SlyPilot flow.

Capture:

- generated packet path
- provider response
- history entry

## Required capture fields

For each run, persist:

- `prompt`
- `mode` (`direct` or `slypilot`)
- `provider`
- `model`
- `response_tokens`
- `timestamp`
- `response_text`
- `packet_path` when `mode = slypilot`
- `task_id` when available

## Result storage

Write one result file per execution under:

- `benchmarks/results/`

Recommended filename:

- `{timestamp}_{mode}_{case_slug}.json`

## Reproducibility rules

- same prompt text
- same provider
- same model
- same environment
- no prompt optimization between direct and SlyPilot runs
- no loader, index, or task packet changes during a benchmark batch

## Suggested execution order

1. direct provider case
2. SlyPilot case
3. compare the two stored outputs

## Notes

- If a run fails, store the failure payload instead of overwriting it.
- Do not invent scores in the capture files.
- Do not normalize away provider differences.
