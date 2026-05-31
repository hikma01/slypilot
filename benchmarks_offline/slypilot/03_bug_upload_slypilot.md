# SlyPilot Capture - 03 Bug Upload SlyScan

## Prompt

Explique comment diagnostiquer un bug upload SlyScan.
Liste les fichiers ou zones à vérifier en priorité.
Ne propose pas de refonte.

## Task Packet

[packets/03_bug_upload_packet.md](../packets/03_bug_upload_packet.md)

## Provider

mock

## Model

mock-offline-v1

## Timestamp

2026-05-31T00:00:00Z

## Response Tokens

108

## Response

The packet makes the upload path explicit, so the answer stays focused on the upload boundary.

Priority checks:

- upload service
- upload route
- storage adapter
- validator
- runtime dependency map for storage and processing edges

Diagnostic order:

1. validate request parsing
2. confirm upload constraints
3. check storage write path
4. inspect downstream failure propagation

This is more actionable than a generic architecture answer because the context is already reduced.
