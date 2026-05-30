# Task Packet Example: Guardrails

```yaml
metadata:
  packet_id: sp-guardrails-01
  project: slypilot
  version: v1
  created_at: "2026-05-31T10:00:00+02:00"
  request_origin: docs
  estimated_raw_context_tokens: 96000
  estimated_packet_tokens: 7200
  context_reduction_ratio: 13.3333
  round_trips: 0
task_type:
  - architecture
input:
  user_request: "Explain whether the SlyPilot architecture is over-engineered."
context:
  project_state: "phase 7 validated"
  relevant_files:
    - README.md
    - docs/01_ARCHITECTURE.md
    - docs/11_CONTEXT_SELECTION_CONTRACT.md
constraints:
  - keep V1 simple
  - preserve provider neutrality
negative_context:
  - no scoring
  - no embeddings
  - no vector search
  - no multi-provider expansion
expected_output:
  response_type: analysis
  deliverable_type: architecture_note
  completion_criteria:
    - stay within documented architecture facts
    - avoid inventing modules
validation:
  review_mode: dry_run
  reviewer: human
system_facts:
  - Selection is deterministic
  - No embeddings are used
  - No vector database is used
  - Context comes from structured-index
  - Loader uses static selection rules
forbidden_assumptions:
  - Do not assume scoring exists
  - Do not assume vector search exists
  - Do not assume embeddings exist
  - Do not assume hidden modules exist
  - Do not assume automatic orchestration exists
  - Do not invent configuration files
  - Do not invent architecture components
out_of_scope:
  - Do not redesign the architecture
  - Do not propose new services
  - Do not propose new frameworks
  - Do not propose infrastructure changes unless explicitly requested
```
