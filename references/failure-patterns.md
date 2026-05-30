# Failure Patterns

## 2026-05-30 - Initial detection stubbed out

- Symptom: `slypilot "corrige bug upload SlyScan" --dry-run` returned no structured detection result because the CLI was a placeholder.
- Root cause: the repository had the package skeleton, but the intake/classifier/project resolution boundary was not implemented yet.
- Proof: `slypilot/cli.py` returned `0` only, and there were no `intake.py`, `classifier.py`, or `project_resolver.py` modules.
- Fix: add a deterministic local intake pipeline, minimal rule files, and a dry-run JSON output path.
- Prevention rule: when a CLI contract is expected, keep a minimal end-to-end detection path in place even before any provider integration.
