# Résultat benchmark Phase 8.1

## Résultats

| Cas | Direct | SlyPilot | Écart |
|---|---:|---:|---:|
| Architecture | 20 | 26 | +6 |
| Bug login Hermes | 18 | 27 | +9 |
| Bug upload SlyScan | 22 | 27 | +5 |

## Écarts

SlyPilot wins all three cases on the manual grid.

The strongest gains are on Hermes login and architecture, where the packet reduces drift and improves contextual focus.

## Forces

- Better scope control
- Better use of fixed context
- Lower structural hallucination risk
- More explicit diagnostic boundaries

## Faiblesses

- Still mock-based
- Not a real provider output
- Technical specificity is limited by the captured responses
- Gains are strongest in framing, not in deep implementation detail

## Verdict

Phase 8.1 validée

## Notes

This benchmark isolates the value of the Task Packet from provider/network effects.
On these controlled captures, the Task Packet improves response quality consistently by reducing entropy and tightening the answer around the intended problem.
