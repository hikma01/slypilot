# Task Packet Example: Architecture

```yaml
metadata:
  packet_id: sp-0003
  project: slypilot
  version: v1
  created_at: "2026-05-30T10:30:00+02:00"
  request_origin: docs
  estimated_raw_context_tokens: 90000
  estimated_packet_tokens: 7000
  context_reduction_ratio: 12.8571
  round_trips: 0
task_type:
  - architecture
input:
  user_request: "Review whether the repository foundation is over-engineered for V1."
context:
  project_state: "phase 0 validated"
  relevant_files:
    - README.md
    - docs/01_ARCHITECTURE.md
    - archi_ops/index.md
constraints:
  - keep V1 simple
  - preserve provider neutrality
negative_context:
  - no dashboard
  - no multi-agent execution
  - no advanced automation
expected_output:
  response_type: review
  deliverable_type: architecture_note
  completion_criteria:
    - identify over-architecture risks
    - suggest simplifications
validation:
  review_mode: dry_run
  reviewer: human
references:
  - docs/08_DECISIONS_LOG.md
```
