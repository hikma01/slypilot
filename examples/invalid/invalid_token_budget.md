# Invalid Task Packet: Token Budget Exceeded

```yaml
metadata:
  packet_id: sp-bad-03
  project: slypilot
  version: v1
  created_at: "2026-05-30T11:30:00+02:00"
  request_origin: cli
  estimated_raw_context_tokens: 250000
  estimated_packet_tokens: 50000
  context_reduction_ratio: 5
  round_trips: 0
task_type:
  - architecture
input:
  user_request: "Carry the entire repo into one provider call."
context:
  relevant_files:
    - README.md
constraints:
  - keep the packet small
negative_context:
  - no oversized payloads
expected_output:
  response_type: review
validation:
  review_mode: dry_run
  reviewer: human
```
