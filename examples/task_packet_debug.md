# Task Packet Example: Debug

```yaml
metadata:
  packet_id: sp-0001
  project: slypilot
  version: v1
  created_at: "2026-05-30T10:00:00+02:00"
  request_origin: cli
  estimated_raw_context_tokens: 120000
  estimated_packet_tokens: 8000
  context_reduction_ratio: 15
  round_trips: 0
task_type:
  - debug
input:
  user_request: "Diagnose why the intake path rejects valid project roots."
context:
  project_state: "PHASE 0 validation"
  relevant_files:
    - docs/01_ARCHITECTURE.md
    - docs/02_TASK_PACKET_STANDARD.md
constraints:
  - keep scope documentation-only
  - no provider integration
negative_context:
  - no sqlite
  - no runtime routing
  - no multi-agent design
expected_output:
  response_type: analysis
  deliverable_type: diagnostic_note
  completion_criteria:
    - identify root cause
    - propose minimal fix
validation:
  review_mode: dry_run
  reviewer: human
references:
  - docs/03_ARCHI_OPS_INDEX.md
notes:
  - example packet for documentation only
```
