"""Command-line entry point for SlyPilot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from slypilot.adapters.deepseek_adapter import DeepSeekAdapterError, run_deepseek_live
from slypilot.coordinator import coordinate_request
from slypilot.archiops_init import initialize_project
from slypilot.intake import build_intake
from slypilot.task_packet_builder import append_history


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    raw_args = list(argv if argv is not None else sys.argv[1:])
    if raw_args and raw_args[0] == "init":
        root = Path.cwd()
        result = initialize_project(root)
        print(f"ARCHI OPS initialized for {result.project_name}.")
        print()
        print("Created:")
        for path in result.created_files:
            print(f"- {path.relative_to(root)}")
        print()
        print("Updated:")
        print(f"- {result.updated_index.relative_to(_repo_root())}")
        if result.warnings:
            print()
            print("Warnings:")
            for warning in result.warnings:
                print(f"- {warning}")
        return 0

    parser = argparse.ArgumentParser(prog="slypilot")
    parser.add_argument("request", nargs="?", help="raw user request to classify")
    parser.add_argument("--dry-run", action="store_true", help="print the initial detection result")
    parser.add_argument("--live-run", action="store_true", help="send the generated packet to the provider")
    args = parser.parse_args(raw_args)

    if not args.request:
        if sys.stdin.isatty():
            print("SlyPilot ready.")
            print("Type your request:")
            try:
                request = input("> ").strip()
            except EOFError:
                return 1
            if not request:
                return 1
            args.request = request
        else:
            request = sys.stdin.read().strip()
            if not request:
                parser.error("a request is required")
            args.request = request

    root = _repo_root()
    intake = build_intake(args.request, root)

    coordinated = coordinate_request(
        intake,
        root,
        current_working_directory=Path.cwd(),
        dry_run=args.dry_run,
        live_run=args.live_run,
    )
    classification = coordinated.intent.classification
    project = coordinated.project

    if classification.task_type == "unknown":
        print("SlyPilot attend une tâche technique.")
        print()
        print("Exemples :")
        print("- analyse architecture SlyPilot")
        print("- corrige bug upload SlyScan")
        print("- explique problème login Hermes")
        return 0

    if not coordinated.decision.allowed:
        print("SlyPilot cannot resolve this request unambiguously.")
        print()
        print(f"requested_project: {project.requested_project}")
        print(f"resolved_project: {project.name}")
        print(f"resolution_source: {project.resolution_source}")
        print(f"confidence: {project.confidence}")
        print(f"fallback_used: {str(project.fallback_used).lower()}")
        print(f"mismatch_detected: {str(project.mismatch_detected).lower()}")
        print()
        print("RESOURCE_TRACE:")
        print(f"  raw_input: {coordinated.resource.raw_input}")
        print(f"  detected_paths: {', '.join(coordinated.resource.detected_paths) if coordinated.resource.detected_paths else 'none'}")
        print(f"  normalized_paths: {', '.join(coordinated.resource.normalized_paths) if coordinated.resource.normalized_paths else 'none'}")
        print(f"  existing_paths: {', '.join(coordinated.resource.existing_paths) if coordinated.resource.existing_paths else 'none'}")
        print(f"  missing_paths: {', '.join(coordinated.resource.missing_paths) if coordinated.resource.missing_paths else 'none'}")
        print(f"  blocked_paths: {', '.join(coordinated.resource.blocked_paths) if coordinated.resource.blocked_paths else 'none'}")
        print(f"  resource_types: {', '.join(coordinated.resource.resource_types) if coordinated.resource.resource_types else 'none'}")
        print(f"  selected_resource: {coordinated.resource.selected_resource}")
        print(f"  intake_status: {coordinated.resource.intake_status}")
        print()
        print("Please confirm the target project explicitly.")
        return 1

    if args.dry_run:
        packet = coordinated.packet
        assert packet is not None
        append_history(
            root / "slypilot" / "storage" / "history.jsonl",
            packet,
            prompt=intake.raw_request,
        )
        print("SLYPILOT DRY RUN")
        print()
        print("Detection:")
        print(f"- task_type: {classification.task_type}")
        print(f"- project: {project.name}")
        print(f"- provider: {project.provider}")
        print(f"- environment: {project.environment}")
        print(f"- requested_project: {project.requested_project}")
        print(f"- resolved_project: {project.name}")
        print(f"- resolution_source: {project.resolution_source}")
        print(f"- confidence: {project.confidence}")
        print(f"- fallback_used: {str(project.fallback_used).lower()}")
        print(f"- mismatch_detected: {str(project.mismatch_detected).lower()}")
        print()
        print("Generated Packet:")
        print(f"- {packet.packet_path.relative_to(root)}")
        print()
        print("RESOURCE_TRACE:")
        print(f"  raw_input: {coordinated.resource.raw_input}")
        print(f"  detected_paths: {', '.join(coordinated.resource.detected_paths) if coordinated.resource.detected_paths else 'none'}")
        print(f"  normalized_paths: {', '.join(coordinated.resource.normalized_paths) if coordinated.resource.normalized_paths else 'none'}")
        print(f"  existing_paths: {', '.join(coordinated.resource.existing_paths) if coordinated.resource.existing_paths else 'none'}")
        print(f"  missing_paths: {', '.join(coordinated.resource.missing_paths) if coordinated.resource.missing_paths else 'none'}")
        print(f"  blocked_paths: {', '.join(coordinated.resource.blocked_paths) if coordinated.resource.blocked_paths else 'none'}")
        print(f"  resource_types: {', '.join(coordinated.resource.resource_types) if coordinated.resource.resource_types else 'none'}")
        print(f"  selected_resource: {coordinated.resource.selected_resource}")
        print(f"  intake_status: {coordinated.resource.intake_status}")
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
    elif args.live_run:
        packet = coordinated.packet
        assert packet is not None
        print("SLYPILOT LIVE RUN")
        print()
        print("Packet:")
        print(f"- {packet.packet_path.relative_to(root)}")
        print(f"- requested_project: {project.requested_project}")
        print(f"- resolved_project: {project.name}")
        print(f"- resolution_source: {project.resolution_source}")
        print(f"- confidence: {project.confidence}")
        print(f"- fallback_used: {str(project.fallback_used).lower()}")
        print(f"- mismatch_detected: {str(project.mismatch_detected).lower()}")
        print()
        print("RESOURCE_TRACE:")
        print(f"  raw_input: {coordinated.resource.raw_input}")
        print(f"  detected_paths: {', '.join(coordinated.resource.detected_paths) if coordinated.resource.detected_paths else 'none'}")
        print(f"  normalized_paths: {', '.join(coordinated.resource.normalized_paths) if coordinated.resource.normalized_paths else 'none'}")
        print(f"  existing_paths: {', '.join(coordinated.resource.existing_paths) if coordinated.resource.existing_paths else 'none'}")
        print(f"  missing_paths: {', '.join(coordinated.resource.missing_paths) if coordinated.resource.missing_paths else 'none'}")
        print(f"  blocked_paths: {', '.join(coordinated.resource.blocked_paths) if coordinated.resource.blocked_paths else 'none'}")
        print(f"  resource_types: {', '.join(coordinated.resource.resource_types) if coordinated.resource.resource_types else 'none'}")
        print(f"  selected_resource: {coordinated.resource.selected_resource}")
        print(f"  intake_status: {coordinated.resource.intake_status}")
        print()
        try:
            response = run_deepseek_live(packet)
        except DeepSeekAdapterError as exc:
            print("Provider error:")
            print(f"- {exc}")
            return 1
        append_history(
            root / "slypilot" / "storage" / "history.jsonl",
            packet,
            prompt=intake.raw_request,
            provider=response.provider,
            status=response.status,
            response_tokens=response.response_tokens,
            response_text=response.response_text,
        )
        print("Provider response:")
        print(response.response_text)
        print()
        print("Response metrics:")
        print(f"- provider: {response.provider}")
        print(f"- model: {response.model}")
        print(f"- response_tokens: {response.response_tokens}")
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
