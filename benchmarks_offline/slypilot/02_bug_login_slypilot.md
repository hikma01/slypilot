# SlyPilot Capture - 02 Bug Login Hermes

## Prompt

Explique le problème probable d'un bug login Hermes.
Donne une stratégie de diagnostic minimale.
Ne modifie pas le périmètre.

## Task Packet

[packets/02_bug_login_packet.md](../packets/02_bug_login_packet.md)

## Provider

mock

## Model

mock-offline-v1

## Timestamp

2026-05-31T00:00:00Z

## Response Tokens

96

## Response

Hermes login issues usually concentrate around authentication, session creation, and token persistence.

Minimal diagnostic path:

1. verify the login endpoint input and response
2. inspect auth middleware and session setup
3. confirm token issuance and storage
4. check redirects and expiry handling

The packet helps by narrowing the response to auth-related files and avoids broad architecture speculation.
