# Invalid Task Packet: Missing Metadata

```yaml
task_type:
  - debug
input:
  user_request: "Investigate the packet contract."
context:
  relevant_files:
    - docs/02_TASK_PACKET_STANDARD.md
constraints:
  - no runtime changes
negative_context:
  - no sqlite
expected_output:
  response_type: analysis
validation:
  review_mode: dry_run
  reviewer: human
```
