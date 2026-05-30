# Failure Patterns

## 2026-05-30 - Initial detection stubbed out

- Symptom: `slypilot "corrige bug upload SlyScan" --dry-run` returned no structured detection result because the CLI was a placeholder.
- Root cause: the repository had the package skeleton, but the intake/classifier/project resolution boundary was not implemented yet.
- Proof: `slypilot/cli.py` returned `0` only, and there were no `intake.py`, `classifier.py`, or `project_resolver.py` modules.
- Fix: add a deterministic local intake pipeline, minimal rule files, and a dry-run JSON output path.
- Prevention rule: when a CLI contract is expected, keep a minimal end-to-end detection path in place even before any provider integration.

## 2026-05-30 - Rule parser misclassified project blocks

- Symptom: `analyse architecture SlyPilot` and `explique problème login Hermes` resolved to the wrong task/project pair.
- Root cause: the local YAML parser interpreted `aliases:` as a project key and fell back to the default project.
- Proof: `load_rules()` produced a bogus `aliases` project entry and omitted proper project ordering.
- Fix: parse the `task_type` and `projects` blocks explicitly by indentation and section, then resolve project aliases from the correct project map.
- Prevention rule: when rules are file-driven, verify the parsed in-memory structure before trusting classification output.

## 2026-05-30 - Packet IDs collided within the same second

- Symptom: multiple dry-run commands generated the same packet filename and overwrote each other.
- Root cause: the packet identifier used second-level timestamps only.
- Proof: three runs executed in rapid succession produced the same `task_YYYYMMDD_HHMMSS.md` name.
- Fix: include microseconds in the task identifier.
- Prevention rule: any file-backed dry-run artifact must have collision-resistant naming from the start.
