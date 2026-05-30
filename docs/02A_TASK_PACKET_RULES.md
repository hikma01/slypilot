# Task Packet Rules

## Packet Valid

A packet is valid when:

- all required sections are present
- `task_type` contains one active value
- `negative_context` is present and explicit
- `expected_output` is present and actionable
- token budget is within limits
- no secret is present

## Packet Invalid

A packet is invalid when:

- a required section is missing
- a required field is missing
- `task_type` contains multiple active values in V1
- the packet contains a secret
- the budget is exceeded
- the packet contradicts its own exclusions

## Budget Exceeded

If `estimated_packet_tokens` exceeds the configured ceiling, the packet must not be sent to a provider.

The packet must be reduced or rejected first.

## Secret Detected

If a secret is detected in the packet:

- block packet creation or submission
- do not persist the secret into History
- redact before any downstream trace

## Negative Context Absent

If `negative_context` is absent, the packet fails validation.

This is a hard failure because exclusions are part of the contract.

## Expected Output Absent

If `expected_output` is absent, the packet fails validation.

The provider cannot be called with an undefined target.

## Section Missing

Any missing mandatory section fails validation.

Mandatory sections:

- `metadata`
- `task_type`
- `input`
- `context`
- `constraints`
- `negative_context`
- `expected_output`
- `validation`
