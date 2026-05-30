# Task Packet Standard

## Objective

The Task Packet is the official normalized handoff document between context reduction and provider invocation.

It exists to:

- reduce raw input into a bounded and auditable payload
- preserve the minimum context required for implementation work
- make provider usage independent from any specific model vendor
- support deterministic review before any provider call

## Standard Structure

The Task Packet is a YAML document.

Required top-level sections:

- `metadata`
- `task_type`
- `input`
- `context`
- `constraints`
- `negative_context`
- `expected_output`
- `validation`

Optional top-level sections:

- `references`
- `notes`
- `history`

## Mandatory Sections

### `metadata`

Required fields:

- `packet_id`
- `project`
- `version`
- `created_at`
- `request_origin`
- `estimated_raw_context_tokens`
- `estimated_packet_tokens`
- `context_reduction_ratio`
- `round_trips`

### `task_type`

V1 decision:

- list format is allowed
- only one active task type is allowed in V1

Example:

```yaml
task_type:
  - debug
```

Multi-type packets are out of scope for V1.

### `input`

Contains the user request in normalized form.

### `context`

Contains only project-relevant context needed for execution.

### `constraints`

Contains operational constraints, safety limits, scope limits, and delivery conditions.

### `negative_context`

Contains explicit exclusions and non-goals.

If `negative_context` is missing, the packet is invalid.

### `expected_output`

Contains the expected provider response shape or the expected work product.

If `expected_output` is missing, the packet is invalid.

### `validation`

Contains the human review gate used during Dry Run.

## Optional Sections

### `references`

Optional links to files, docs, issues, or decision records.

### `notes`

Optional clarifications that do not change the packet contract.

### `history`

Optional trace of prior attempts or resumes.

`round_trips` must be stored in history when resume state exists.

## Constraints

- The packet must remain provider-neutral.
- The packet must not embed business logic.
- The packet must not include hidden automation rules.
- The packet must not contain secrets.
- The packet must remain reviewable by humans before provider submission.

## Token Budget

### `estimated_packet_tokens`

`estimated_packet_tokens` is computed by the Task Packet Builder after full assembly.

Method:

- local tokenization
- estimated after normalization and assembly

### `estimated_raw_context_tokens`

Estimated total token size of the unfiltered source context before reduction.

### `context_reduction_ratio`

Official formula:

```txt
estimated_raw_context_tokens / estimated_packet_tokens
```

Example:

```txt
120000 / 8000 = 15
```

## Negative Context

`negative_context` lists:

- excluded files
- excluded assumptions
- excluded features
- excluded providers
- excluded execution paths

Missing negative context is a contract violation.

## Expected Output

`expected_output` must specify at least one of the following:

- response type
- deliverable type
- validation target
- completion criteria

The section may be concise, but it cannot be absent.

## Validation

Validation in V1 is documentary and human-reviewed.

Rules:

- packet completeness is checked against the schema
- secret detection blocks the packet
- Dry Run is the human review point
- automated provider output validation is out of scope for V1

## Invalid Cases

A packet is invalid if:

- `metadata` is missing
- `task_type` is missing
- `negative_context` is missing
- `expected_output` is missing
- `estimated_packet_tokens` is missing
- `round_trips` is missing
- a secret is present
- the declared scope conflicts with documented exclusions
- the packet exceeds the allowed budget

## REDACTOR POLICY

- Secret detected: block the packet
- Secret in provider response: mask before writing to History

## Validation Scope Note

Validation of provider output remains human inspection through Dry Run in V1.

Automatic post-generation validation is explicitly out of scope.
