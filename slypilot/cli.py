"""Command-line entry point for SlyPilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from slypilot.intake import build_intake
from slypilot.classifier import classify_intake
from slypilot.project_resolver import resolve_project
from slypilot.task_packet_builder import append_history, build_task_packet


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

    if args.dry_run:
        packet = build_task_packet(intake, classification, project, root)
        append_history(root / "slypilot" / "storage" / "history.jsonl", packet)
        print("SLYPILOT DRY RUN")
        print()
        print("Detection:")
        print(f"- task_type: {classification.task_type}")
        print(f"- project: {project.name}")
        print(f"- provider: {project.provider}")
        print(f"- environment: {project.environment}")
        print()
        print("Generated Packet:")
        print(f"- {packet.packet_path.relative_to(root)}")
        print()
        print("Warnings:")
        if packet.warnings:
            for warning in packet.warnings:
                print(f"- {warning}")
        else:
            print("- none")
        print()
        print("--- TASK PACKET ---")
        print(packet.content)
    else:
        result = {
            "task_type": classification.task_type,
            "project": project.name,
            "provider": project.provider,
            "environment": project.environment,
        }
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
