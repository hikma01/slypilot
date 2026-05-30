# Task Packet Guardrails

Date: 2026-05-31

Purpose: reduce structural hallucinations by making explicit what is real, what is forbidden, and what is out of scope.

## Guardrail sections

The Task Packet includes three static sections:

- `SYSTEM_FACTS`
- `FORBIDDEN_ASSUMPTIONS`
- `OUT_OF_SCOPE`

## SYSTEM_FACTS

Contains only verified facts from the current SlyPilot architecture.

Example facts:

- Selection is deterministic
- No embeddings are used
- No vector database is used
- Context comes from structured-index
- Loader uses static selection rules

## FORBIDDEN_ASSUMPTIONS

Contains explicit statements the provider must not invent.

Example assumptions to forbid:

- Do not assume scoring exists
- Do not assume vector search exists
- Do not assume embeddings exist
- Do not assume hidden modules exist
- Do not assume automatic orchestration exists
- Do not invent configuration files
- Do not invent architecture components

## OUT_OF_SCOPE

Contains what the provider must not expand into unless asked.

Example out-of-scope items:

- Do not redesign the architecture
- Do not propose new services
- Do not propose new frameworks
- Do not propose infrastructure changes unless explicitly requested

## Expected effect

These guardrails are intended to:

- reduce extrapolations
- reduce unsupported architecture invention
- keep the answer anchored to observed facts
- preserve analytical ability while constraining speculation

## Contract rule

The guardrails must stay:

- short
- static
- deterministic
- non-LLM

They are a packet contract addition, not a new reasoning engine.
