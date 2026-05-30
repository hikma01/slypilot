"""Minimal Task Packet Builder for SlyPilot V1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

from slypilot.classifier import Classification
from slypilot.intake import Intake
from slypilot.project_resolver import ResolvedProject
from slypilot.utils.token_estimator import estimate_tokens


@dataclass(frozen=True)
class BuiltPacket:
    packet_id: str
    task_id: str
    packet_path: Path
    content: str
    warnings: list[str]
    metadata: dict[str, object]


def build_task_packet(
    intake: Intake,
    classification: Classification,
    project: ResolvedProject,
    repository_root: Path,
) -> BuiltPacket:
    warnings: list[str] = []
    task_id = _task_id()
    packet_id = task_id
    generated_dir = repository_root / "slypilot" / "packets" / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    packet_path = generated_dir / f"{task_id}.md"

    archi_ops_path = repository_root / "archi_ops" / "index.md"
    archi_ops_summary, negative_context = _load_archi_ops(archi_ops_path, warnings)

    selected_files = _selected_files(classification.task_type, project.name)
    selected_lines_count = _selected_lines_count(selected_files)
    raw_context = _build_raw_context(intake.raw_request, archi_ops_summary, selected_files)

    content = _render_packet(
        project=project,
        classification=classification,
        intake=intake,
        packet_id=packet_id,
        task_id=task_id,
        archi_ops_summary=archi_ops_summary,
        negative_context=negative_context,
        selected_files=selected_files,
        raw_context=raw_context,
        selected_lines_count=selected_lines_count,
    )

    packet_path.write_text(content, encoding="utf-8")

    estimated_packet_tokens = estimate_tokens(content)
    estimated_raw_context_tokens = estimate_tokens(raw_context)
    context_reduction_ratio = (
        None
        if estimated_raw_context_tokens == 0
        else round(estimated_raw_context_tokens / estimated_packet_tokens, 4)
    )

    metadata = {
        "project": project.name,
        "environment": project.environment,
        "provider": project.provider,
        "task_type": classification.task_type,
        "dry_run": True,
        "estimated_raw_context_tokens": estimated_raw_context_tokens,
        "estimated_packet_tokens": estimated_packet_tokens,
        "context_reduction_ratio": context_reduction_ratio,
        "selected_files_count": len(selected_files),
        "selected_lines_count": selected_lines_count,
        "round_trips": 0,
        "negative_context": negative_context,
    }

    return BuiltPacket(
        packet_id=packet_id,
        task_id=task_id,
        packet_path=packet_path,
        content=content,
        warnings=warnings,
        metadata=metadata,
    )


def _task_id() -> str:
    return datetime.now(timezone.utc).strftime("task_%Y%m%d_%H%M%S_%f")


def _load_archi_ops(path: Path, warnings: list[str]) -> tuple[str, list[str]]:
    if not path.exists():
        warnings.append(f"ARCHI OPS index missing: {path}")
        return "ARCHI OPS index unavailable.", []

    content = path.read_text(encoding="utf-8")
    negative_context: list[str] = []
    in_negative_context = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == "## Negative Context":
            in_negative_context = True
            continue
        if stripped.startswith("## ") and stripped != "## Negative Context":
            in_negative_context = False
        if in_negative_context and stripped.startswith("- "):
            negative_context.append(stripped[2:].strip())

    summary = "ARCHI OPS minimal index loaded."
    return summary, negative_context


def _selected_files(task_type: str, project: str) -> list[str]:
    files = ["archi_ops/index.md"]
    if project == "slypilot":
        files.append("docs/01_ARCHITECTURE.md")
    elif project == "hermes":
        files.append("docs/04_SECURITY.md")
    else:
        files.append("docs/03_ARCHI_OPS_INDEX.md")

    if task_type == "architecture":
        files.append("docs/01_ARCHITECTURE.md")
    elif task_type == "debug":
        files.append("docs/02_TASK_PACKET_STANDARD.md")
    elif task_type == "explain":
        files.append("docs/00_PROJECT_OVERVIEW.md")

    return list(dict.fromkeys(files))


def _selected_lines_count(files: list[str]) -> int:
    # V1 intentionally uses a simple, bounded proxy.
    return sum(25 if path.endswith(".md") else 10 for path in files)


def _build_raw_context(raw_request: str, archi_ops_summary: str, selected_files: list[str]) -> str:
    return "\n".join(
        [
            raw_request,
            archi_ops_summary,
            "\n".join(selected_files),
        ]
    )


def _render_packet(
    project: ResolvedProject,
    classification: Classification,
    intake: Intake,
    packet_id: str,
    task_id: str,
    archi_ops_summary: str,
    negative_context: list[str],
    selected_files: list[str],
    raw_context: str,
    selected_lines_count: int,
) -> str:
    estimated_raw_context_tokens = estimate_tokens(raw_context)
    estimated_packet_tokens = estimate_tokens(
        "\n".join(
            [
                packet_id,
                task_id,
                project.name,
                project.environment,
                project.provider,
                classification.task_type,
                intake.raw_request,
                archi_ops_summary,
                "\n".join(negative_context),
                "\n".join(selected_files),
            ]
        )
    )
    negative_context_lines = [f"- {item}" for item in negative_context] or ["- none"]
    body_lines = [
            "# TASK PACKET",
            "",
            "## METADATA",
            "",
            f"packet_id: {packet_id}",
            f"task_id: {task_id}",
            f"project: {project.name}",
            f"environment: {project.environment}",
            f"provider: {project.provider}",
            f"task_type: {classification.task_type}",
            "dry_run: true",
            "",
            "---",
            "",
            "## CONSTRAINTS",
            "",
            "max_files: 5",
            "max_lines_per_file: 300",
            "no_global_scan: true",
            "no_secret: true",
            "no_system_access: true",
            "",
            "---",
            "",
            "## METRICS",
            "",
            f"estimated_raw_context_tokens: {estimated_raw_context_tokens}",
            f"estimated_packet_tokens: {estimated_packet_tokens}",
            f"context_reduction_ratio: {round(estimated_raw_context_tokens / max(1, estimated_packet_tokens), 4) if estimated_raw_context_tokens else 'null'}",
            f"selected_files_count: {len(selected_files)}",
            f"selected_lines_count: {selected_lines_count}",
            "round_trips: 0",
            "",
            "---",
            "",
            "## NEGATIVE CONTEXT",
            "",
            *negative_context_lines,
            "",
            "---",
            "",
            "## INPUTS",
            "",
            f"user_request: {intake.raw_request}",
            f"detected_keywords: {classification.task_type}",
            f"selected_files: {', '.join(selected_files)}",
            "loaded_maps: archi_ops/index.md",
            "logs: none",
            "",
            "---",
            "",
            "## ARCHI OPS CONTEXT",
            "",
            f"summary: {archi_ops_summary}",
            f"known_issues: {', '.join(item for item in negative_context[:2]) if negative_context else 'none'}",
            "",
            "---",
            "",
            "## USER REQUEST",
            "",
            intake.raw_request,
            "",
            "---",
            "",
            "## EXPECTED OUTPUT",
            "",
            "1. Diagnostic",
            "2. Cause probable",
            "3. Correctif minimal",
            "4. Tests à exécuter",
            "5. Risques",
        ]
    body = "\n".join(body_lines)
    return body


def append_history(history_path: Path, packet: BuiltPacket) -> None:
    history_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "task_id": packet.task_id,
        "project": packet.metadata["project"],
        "task_type": packet.metadata["task_type"],
        "provider": packet.metadata["provider"],
        "environment": packet.metadata["environment"],
        "dry_run": packet.metadata["dry_run"],
        "packet_path": str(packet.packet_path.relative_to(history_path.parents[1])),
        "status": "packet_generated",
    }
    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
