# Direct Capture - 03 Bug Upload SlyScan

## Prompt

Explique comment diagnostiquer un bug upload SlyScan.
Liste les fichiers ou zones à vérifier en priorité.
Ne propose pas de refonte.

## Provider

mock

## Model

mock-offline-v1

## Timestamp

2026-05-31T00:00:00Z

## Response Tokens

78

## Packet Path

none

## Response

Check the upload boundary first:

- upload service
- upload route
- storage adapter
- validator

Then confirm:

1. file size and type validation
2. request parsing
3. storage write errors
4. downstream processing status

Keep the investigation close to the upload entrypoint.
