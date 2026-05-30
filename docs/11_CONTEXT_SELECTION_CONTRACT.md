# Context Selection Contract

Date: 2026-05-31

This document defines the official SlyPilot contract for context selection.
It does not define loader code.

## Scope

SlyPilot may select context only through ARCHI OPS.
It must not read project files directly outside the ARCHI OPS path.

## Canonical term

Use `structured-index` as the official term.

Reason:

- it is broader than tagging
- it stays compatible with deterministic selection
- it avoids implying a semantic search engine

## Input contract

- `project_id`: project identity
- `task_type`: task family
- `context_profile`: `minimal`, `standard`, or `premium`
- `intent_keywords`: free-form intent hints

## Output contract

- `files`: ordered file selection with reason and extracted content
- `maps`: ordered map selection
- `incident_cards`: ordered incident card selection
- `metadata`: selection summary

## Context profiles

### minimal

- `max_files = 3`
- `max_lines = 200`

Use when the request is narrow and the issue is already well framed.

### standard

- `max_files = 8`
- `max_lines = 500`

Use for ordinary work where the first pass may need a little more evidence.

### premium

- `max_files = 15`
- `max_lines = 1000`

Use only when the incident is broad, repetitive, or known to require more context.

## V1 selection algorithm

1. Read the structured index.
2. Filter by `task_type`.
3. Filter by tags or selection hints.
4. Sort by `weight`.
5. Apply the profile limits.
6. Return the selected context.

## Constraints

- no repo scan
- only index files
- respect context profile
- deterministic selection
- no loader code
- no embeddings
- no vector DB
- no similarity search
- no dynamic scoring
- no LLM selector
- no advanced auto-routing

## Index staleness risk

### How to detect

- the selected files no longer exist
- the index references a path that has moved
- the index returns a file that is no longer relevant to the current task type
- a repeated incident keeps requiring manual correction

### How to signal

- mark the entry as stale in the index
- record the stale reason in the history trace
- exclude stale entries from default selection

### How to maintain

- review index entries when a file moves or is renamed
- update selection weight only when the relevance has been validated
- keep the index narrow and current
- do not expand the index with speculative entries

## history.jsonl usage

`history.jsonl` may be used later as a simple maintenance source for:

- `bug_count`
- `last_used`
- `last_selected`

For now, these fields remain documentary only.
They must not drive automated selection.

## Recommendation

The contract is intentionally small.
The most useful path is to keep the selection deterministic and the index manually maintainable.
