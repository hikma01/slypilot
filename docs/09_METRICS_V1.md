# Metrics V1

## Purpose

This document defines the official metrics used to validate or invalidate the SlyPilot V1 hypothesis:

- contextual reduction improves quality
- contextual reduction improves stability
- contextual reduction reduces cost
- contextual reduction improves speed
- contextual reduction reduces round trips

## Measurement Principles

- metrics must be defined once
- formulas must be explicit
- thresholds must be stated for V1
- metrics must support comparison against a direct provider baseline
- metrics must remain provider-neutral where possible

## Official Metrics

### `context_reduction_ratio`

Formula:

```txt
estimated_raw_context_tokens / estimated_packet_tokens
```

V1 thresholds:

- minimum acceptable: `5`
- target: `10`
- ambitious target: `15`

### `selected_files_count`

Definition:

- number of files included in `selected_files`

V1 limits:

- debug: `<= 5`
- patch: `<= 5`
- architecture: `<= 10`
- audit: `<= 15`

### `selected_lines_count`

Definition:

- total number of lines across all selected files

V1 limits:

- debug: `<= 300`
- patch: `<= 300`
- architecture: `<= 800`
- audit: `<= 1000`

### `estimated_packet_tokens`

Definition:

- token count of the fully assembled packet after local tokenization

V1 rule:

- always present
- one tokenization method only for the whole project

### `round_trips`

Definition:

- number of re-executions for the same `task_id`

V1 target:

- `<= 2`

### `success_rate`

Formula:

```txt
resolved_tasks / executed_tasks
```

Allowed statuses:

- `resolved`
- `partial`
- `failed`

V1 target:

- `>= 70%`

### `time_to_packet`

Formula:

```txt
timestamp_packet_created - timestamp_request_received
```

V1 target:

- `< 5 seconds`

### `time_to_response`

Formula:

```txt
timestamp_response_received - timestamp_request_received
```

V1 rule:

- measured in Phase 1
- no hard target yet

### `provider_cost_estimate`

Formula:

```txt
input_tokens + output_tokens
```

Usage:

- compare before and after context reduction

### `secret_detection_count`

Definition:

- number of secrets detected by the Redactor

V1 target:

- `0` secret transmitted to the provider

## Official Validation Table

| Metric | Priority | V1 Validation |
|--------|----------|---------------|
| context_reduction_ratio | critical | `>= 10` |
| selected_files_count | critical | respect limits |
| selected_lines_count | critical | respect limits |
| estimated_packet_tokens | critical | always present |
| round_trips | major | `<= 2` |
| success_rate | major | `>= 70%` |
| time_to_packet | important | `< 5s` |
| time_to_response | important | measured |
| provider_cost_estimate | important | measured |
| secret_detection_count | critical | `0` leak |

## Validation Criteria

Phase 0 is valid when:

- each metric has a unique definition
- each formula is explicit
- each V1 threshold is documented
- the metrics can validate the central hypothesis

SlyPilot V1 is valid when:

- `context_reduction_ratio >= 10`
- `round_trips <= 2`
- `success_rate >= 70%`
- no secret reaches the provider
- task packets are generated on real cases
- the reduced workflow improves results versus direct provider usage

