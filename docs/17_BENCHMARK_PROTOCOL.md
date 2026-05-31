# Benchmark Protocol

Date: 2026-05-31

## Objective

Compare direct-provider responses versus SlyPilot-assisted responses on the same prompts.

The benchmark does not change production code.

## Scope

This protocol captures:

- prompt
- provider
- model
- timestamp
- response_tokens
- packet_path
- response_text

It does not:

- score automatically
- optimize prompts
- add provider routing
- alter loader, index, task packet, or adapter logic

## Modes

### Direct provider

Send the raw user prompt directly to the provider.

Store results in `benchmarks/direct/`.

### SlyPilot

Send the same prompt through:

- classifier
- project resolver
- ARCHI OPS loader
- task packet builder
- DeepSeek adapter

Store results in `benchmarks/slypilot/`.

## Prompts

Use these exact prompts:

1. `Analyse l'architecture de SlyPilot. Explique son rôle, ses limites et les risques de dérive. Ne propose pas de nouvelle architecture.`
2. `Explique le problème probable d'un bug login Hermes. Donne une stratégie de diagnostic minimale. Ne modifie pas le périmètre.`
3. `Explique comment diagnostiquer un bug upload SlyScan. Liste les fichiers ou zones à vérifier en priorité. Ne propose pas de refonte.`

## Results directories

- `benchmarks/direct/`
- `benchmarks/slypilot/`
- `benchmarks/evaluations/`

## Evaluation method

Use a manual grid with the following criteria:

- respect du périmètre
- utilisation correcte du contexte
- absence d'hallucination structurelle
- précision technique
- réponse actionnable
- simplicité
- réduction d'entropie

Each criterion is scored from `0` to `4`.

Maximum score per response: `28`.

## Limits

- A failed run must still be written to disk.
- Do not invent missing responses.
- Do not normalize away provider differences.
- Do not modify benchmark prompts during a run.

## Required outputs

- direct captures for each prompt
- SlyPilot captures for each prompt
- evaluation files for each prompt
- final benchmark summary
