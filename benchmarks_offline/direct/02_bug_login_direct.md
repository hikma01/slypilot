# Direct Capture - 02 Bug Login Hermes

## Prompt

Explique le problème probable d'un bug login Hermes.
Donne une stratégie de diagnostic minimale.
Ne modifie pas le périmètre.

## Provider

mock

## Model

mock-offline-v1

## Timestamp

2026-05-31T00:00:00Z

## Response Tokens

80

## Packet Path

none

## Response

The most likely login bug areas are authentication flow, session handling, and token validation.

Minimal diagnostic strategy:

1. confirm the failing login step
2. check request payload and response status
3. verify session creation or token issuance
4. inspect auth middleware and redirects

Start from the login handler and the session/token boundary.
