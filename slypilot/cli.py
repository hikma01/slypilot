"""Command-line entry point for SlyPilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from slypilot.intake import build_intake
from slypilot.classifier import classify_intake
from slypilot.project_resolver import resolve_project


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="slypilot")
    parser.add_argument("request", help="raw user request to classify")
    parser.add_argument("--dry-run", action="store_true", help="print the initial detection result")
    args = parser.parse_args(argv)

    root = _repo_root()
    intake = build_intake(args.request, root)
    classification = classify_intake(intake, root)
    project = resolve_project(classification, root)

    result = {
        "task_type": classification.task_type,
        "project": project.name,
        "provider": project.provider,
        "environment": project.environment,
    }

    if args.dry_run:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
