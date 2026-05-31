# Cas testé

01_architecture

# Réponse Provider direct

SlyPilot is a coordination pipeline that turns a raw request into a task packet before any provider call.

Its role is to reduce context entropy by filtering project knowledge through a deterministic index and a fixed packet builder.

Limits:

- it does not replace the provider
- it does not reason dynamically about relevance
- it does not scan the full repository at runtime

Risks of drift:

- adding hidden heuristics
- expanding the loader into a semantic router
- letting the packet become a second architecture instead of a compact handoff

Keep it small, deterministic, and explicit.

# Réponse SlyPilot

SlyPilot is a deterministic context-reduction layer, not a new architecture.

What it does well:

- keeps the prompt narrow
- selects context from an index
- adds guardrails that constrain unsupported assumptions

Limits:

- it depends on the quality of the index
- it cannot repair a missing or stale knowledge base
- it should not become a second reasoning system

Main drift risk:

turning the packet into a hidden orchestration layer instead of a compact handoff.

# Tableau comparatif

| Critère | Direct | SlyPilot | Commentaire |
|---|---:|---:|---|
| Respect du périmètre | 3 | 4 | SlyPilot stays closer to the requested framing. |
| Utilisation correcte du contexte | 3 | 4 | SlyPilot uses explicit context and guardrails. |
| Absence d'hallucination structurelle | 4 | 4 | Both stay disciplined in this mock run. |
| Précision technique | 3 | 3 | Both are technically sound but still generic. |
| Réponse actionnable | 2 | 3 | SlyPilot gives slightly clearer guidance. |
| Simplicité | 3 | 4 | SlyPilot is tighter and more focused. |
| Réduction d'entropie | 2 | 4 | SlyPilot better constrains unsupported expansion. |

# Verdict

Gagnant : SlyPilot
Écart : 6 points
Raison : The packet-focused version is narrower, more explicit about limits, and better at preventing drift.
