# History Simple

Date: 2026-05-31

## Goal

Keep a minimal execution history for SlyPilot V1.

The history is intentionally small and append-only.
It records the prompt, the generated packet reference, and the provider response when available.

## Storage format

`slypilot/storage/history.jsonl`

Each line is one JSON object.

## Minimal fields

- `task_id`
- `prompt`
- `project`
- `task_type`
- `provider`
- `environment`
- `dry_run`
- `packet_path`
- `status`

Optional live-run fields:

- `response_tokens`
- `response_text`

## Rules

- no embeddings
- no vector search
- no database
- no memory graph
- no automatic summarization
- no provider routing

## Read path

History can be read with a simple JSONL parser.

Supported uses:

- inspect recent executions
- confirm packet generation
- inspect the last provider response

## Not in scope

- ranking executions
- clustering prompts
- semantic recall
- automatic reuse of past answers
- cross-task memory

## Recommendation

Keep history append-only and explicit.
If history ever becomes useful for selection, that decision must be justified by field evidence, not by architecture preference.
