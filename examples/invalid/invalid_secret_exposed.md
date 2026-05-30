# Invalid Task Packet: Secret Exposed

```yaml
metadata:
  packet_id: sp-bad-02
  project: slypilot
  version: v1
  created_at: "2026-05-30T11:15:00+02:00"
  request_origin: cli
  estimated_raw_context_tokens: 30000
  estimated_packet_tokens: 5000
  context_reduction_ratio: 6
  round_trips: 0
task_type:
  - patch
input:
  user_request: "Patch the adapter."
context:
  relevant_files:
    - slypilot/adapters/__init__.py
constraints:
  - no provider details
negative_context:
  - no runtime adapter
expected_output:
  response_type: patch_plan
  secret: "sk-live-example-token"
validation:
  review_mode: dry_run
  reviewer: human
```
