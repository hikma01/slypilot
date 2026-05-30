# Task Packet Example: Patch

```yaml
metadata:
  packet_id: sp-0002
  project: slypilot
  version: v1
  created_at: "2026-05-30T10:15:00+02:00"
  request_origin: cli
  estimated_raw_context_tokens: 64000
  estimated_packet_tokens: 6000
  context_reduction_ratio: 10.6667
  round_trips: 1
task_type:
  - patch
input:
  user_request: "Add missing documentation files and update the structure tests."
context:
  project_state: "repository foundation"
  relevant_files:
    - tests/test_structure.py
    - docs/02_TASK_PACKET_STANDARD.md
constraints:
  - no business logic
  - no runtime provider adapter
negative_context:
  - no sqlite
  - no orchestration engine
  - no automated provider validation
expected_output:
  response_type: patch_plan
  deliverable_type: file_edits
  completion_criteria:
    - list files to change
    - preserve repository scope
validation:
  review_mode: dry_run
  reviewer: human
history:
  round_trips: 1
  notes:
    - resume after initial review
```
