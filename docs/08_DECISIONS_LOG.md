# Decisions Log

## 2026-05-30

- Created a minimal repository foundation only.
- Deferred all business logic and provider integration.
- Kept ARCHI OPS as a structural knowledge directory rather than a runtime system.
- Added an official V1 metrics document to formalize the validation contract.
- Added a minimal Task Packet Builder and structured dry-run output for Phase 3.

## 2026-05-31

- Added a deterministic ARCHI OPS loader with a local index contract.
- Replaced ad hoc packet file selection with indexed selection.
- Added packet metrics for selected files, selected lines, and excluded files.
- Kept `intent_keywords` out of V1 selection by explicit decision.
- Added loader-focused tests using the Python standard library.
- Relevance validation showed strong architecture results but weak SlyScan bug coverage.
- Provider integration remains deferred until the index is strengthened.
- Hermes security validation confirmed the issue was missing coverage plus budget representation.
- Phase 9 keeps history minimal: append-only JSONL with prompt, packet reference, and optional response text.
