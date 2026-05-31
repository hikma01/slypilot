# Direct Capture - 01 Architecture

## Prompt

Analyse l'architecture de SlyPilot.
Explique son rôle, ses limites et les risques de dérive.
Ne propose pas de nouvelle architecture.

## Provider

mock

## Model

mock-offline-v1

## Timestamp

2026-05-31T00:00:00Z

## Response Tokens

92

## Packet Path

none

## Response

SlyPilot is a coordination pipeline that turns a raw request into a task packet before any provider call.

Its role is to reduce context entropy by filtering project knowledge through a deterministic index and a fixed packet builder.

Limits:

- it does not replace the provider
- it does not reason dynamically about relevance
- it does not scan the full repository at runtime

Risks of drift:

- adding hidden heuristics
- expanding the loader into a semantic router
- letting the packet become a second architecture instead of a compact handoff

Keep it small, deterministic, and explicit.
