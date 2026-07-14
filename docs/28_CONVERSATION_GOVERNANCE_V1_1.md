# Conversation Runtime V1.1

## Objectif

Ajouter la gouvernance des sessions conversationnelles de SlyPilot sans modifier le coordinateur, ARCHI OPS, le filesystem tool, le task packet ou les providers.

## Fonctionnalités

- listing des sessions
- consultation de la session courante ou la plus récente
- reprise d'une session existante
- reprise de la dernière session
- conservation d'un index `runtime/sessions/index.json`
- résumé de session à la fermeture
- politique de rétention limitée

## Commandes

- `slypilot sessions`
- `slypilot session`
- `slypilot resume <session_id>`
- `slypilot resume last`
- `slypilot history`
- `slypilot history <project>`

## Stockage

- événements: `runtime/sessions/<session_id>.jsonl`
- index: `runtime/sessions/index.json`
- résumés: `runtime/sessions/summaries/<session_id>.json`

## Garde-fous

- maximum 1000 sessions
- conservation maximale 90 jours
- pas de provider
- pas d'OCR
- pas d'embeddings
- pas de multi-agent

