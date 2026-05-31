"""Minimal Task Packet Builder for SlyPilot V1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

from slypilot.archi_ops_loader import load_archi_ops_context
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
    loader_result = load_archi_ops_context(
        repository_root=repository_root,
        project_id=project.name,
        task_type=classification.task_type,
        context_profile=_context_profile_for_project(project.name),
    )
    warnings.extend(loader_result.warnings)

    selected_files = [item.path for item in loader_result.files]
    selected_maps = [item.path for item in loader_result.maps]
    selection_reasons = [f"{item.path}: {item.reason}" for item in [*loader_result.files, *loader_result.maps]]
    selected_lines_count = int(loader_result.metadata["selected_lines_count"])
    raw_context = _build_raw_context(intake.raw_request, archi_ops_summary, selected_files, selected_maps)

    content = _render_packet(
        project=project,
        classification=classification,
        intake=intake,
        packet_id=packet_id,
        task_id=task_id,
        archi_ops_summary=archi_ops_summary,
        negative_context=negative_context,
        selected_files=selected_files,
        selected_maps=selected_maps,
        selection_reasons=selection_reasons,
        raw_context=raw_context,
        selected_lines_count=selected_lines_count,
        loader_metadata=loader_result.metadata,
    )

    packet_path.write_text(content, encoding="utf-8")

    estimated_packet_tokens = estimate_tokens(content)
    estimated_raw_context_tokens = int(loader_result.metadata["estimated_raw_context_tokens"])
    context_reduction_ratio = (
        None
        if estimated_raw_context_tokens == 0
        else round(estimated_raw_context_tokens / estimated_packet_tokens, 4)
    )

    metadata = {
        "project": project.name,
        "environment": project.environment,
        "provider": project.provider,
        "prompt": intake.raw_request,
        "task_type": classification.task_type,
        "dry_run": True,
        "estimated_raw_context_tokens": estimated_raw_context_tokens,
        "estimated_packet_tokens": estimated_packet_tokens,
        "context_reduction_ratio": context_reduction_ratio,
        "selected_files_count": len(selected_files),
        "selected_lines_count": selected_lines_count,
        "files_excluded_count": int(loader_result.metadata["files_excluded"]),
        "round_trips": 0,
        "negative_context": negative_context,
        "selected_maps": selected_maps,
        "selection_reasons": selection_reasons,
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


def _context_profile_for_project(project_name: str) -> str:
    if project_name == "slypilot":
        return "standard"
    if project_name == "slyscan":
        return "premium"
    return "minimal"


def _build_raw_context(
    raw_request: str,
    archi_ops_summary: str,
    selected_files: list[str],
    selected_maps: list[str],
) -> str:
    return "\n".join(
        [
            raw_request,
            archi_ops_summary,
            "\n".join(selected_files),
            "\n".join(selected_maps),
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
    selected_maps: list[str],
    selection_reasons: list[str],
    raw_context: str,
    selected_lines_count: int,
    loader_metadata: dict[str, object],
) -> str:
    estimated_raw_context_tokens = int(loader_metadata["estimated_raw_context_tokens"])
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
                "\n".join(selected_maps),
                "\n".join(selection_reasons),
            ]
        )
    )
    negative_context_lines = [f"- {item}" for item in negative_context] or ["- none"]
    system_facts_lines = [
        "- Selection is deterministic",
        "- No embeddings are used",
        "- No vector database is used",
        "- Context comes from structured-index",
        "- Loader uses static selection rules",
    ]
    forbidden_assumptions_lines = [
        "- Do not assume scoring exists",
        "- Do not assume vector search exists",
        "- Do not assume embeddings exist",
        "- Do not assume hidden modules exist",
        "- Do not assume automatic orchestration exists",
        "- Do not invent configuration files",
        "- Do not invent architecture components",
    ]
    out_of_scope_lines = [
        "- Do not redesign the architecture",
        "- Do not propose new services",
        "- Do not propose new frameworks",
        "- Do not propose infrastructure changes unless explicitly requested",
    ]
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
        "## SYSTEM_FACTS",
        "",
        *system_facts_lines,
        "",
        "---",
        "",
        "## FORBIDDEN_ASSUMPTIONS",
        "",
        *forbidden_assumptions_lines,
        "",
        "---",
        "",
        "## OUT_OF_SCOPE",
        "",
        *out_of_scope_lines,
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
        f"files_excluded_count: {loader_metadata['files_excluded']}",
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
        f"selected_maps: {', '.join(selected_maps)}",
        f"selection_reasons: {', '.join(selection_reasons) if selection_reasons else 'none'}",
        "loaded_maps: archi_ops/index.yaml",
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
    return "\n".join(body_lines)


def append_history(
    history_path: Path,
    packet: BuiltPacket,
    prompt: str | None = None,
    provider: str | None = None,
    status: str = "packet_generated",
    response_tokens: int | None = None,
    response_text: str | None = None,
) -> None:
    history_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "task_id": packet.task_id,
        "prompt": prompt or packet.metadata.get("prompt"),
        "project": packet.metadata["project"],
        "task_type": packet.metadata["task_type"],
        "provider": provider or packet.metadata["provider"],
        "environment": packet.metadata["environment"],
        "dry_run": packet.metadata["dry_run"],
        "packet_path": str(packet.packet_path.relative_to(history_path.parents[1])),
        "status": status,
    }
    if response_tokens is not None:
        payload["response_tokens"] = response_tokens
    if response_text is not None:
        payload["response_text"] = response_text
    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
