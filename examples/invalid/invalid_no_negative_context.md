# Invalid Task Packet: No Negative Context

```yaml
metadata:
  packet_id: sp-bad-01
  project: slypilot
  version: v1
  created_at: "2026-05-30T11:00:00+02:00"
  request_origin: cli
  estimated_raw_context_tokens: 30000
  estimated_packet_tokens: 5000
  context_reduction_ratio: 6
  round_trips: 0
task_type:
  - debug
input:
  user_request: "Check packet contract compliance."
context:
  relevant_files:
    - docs/02_TASK_PACKET_STANDARD.md
constraints:
  - documentation only
expected_output:
  response_type: analysis
validation:
  review_mode: dry_run
  reviewer: human
```
