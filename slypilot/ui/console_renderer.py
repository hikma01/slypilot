"""Console message renderer for conversational UX."""

from __future__ import annotations

from .chat_renderer import render_slypilot_message, render_user_message
from .style import hr, dim
from .trace_renderer import render_coordinator_trace, render_resource_trace


def render_banner() -> str:
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🤖 SlyPilot",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        "Assistant de coordination technique.",
        "",
        "Exemples :",
        "",
        "• analyse le projet /Users/.../MonProjet",
        "• analyse architecture SlyPilot",
        "• explique le problème login Hermes",
        "• corrige le bug upload SlyScan",
        "",
        "Tape ta demande :",
    ]
    return "\n".join(lines)


def render_init_message(project_name: str, created_paths: list[str]) -> str:
    created_lines = [f"- {path}" for path in created_paths] if created_paths else ["- aucun"]
    lines = [
        render_slypilot_message(
            "Projet détecté :",
            [project_name],
        ),
        "",
        "Statut :",
        "ARCHI OPS initialisé",
        "",
        "Créé :",
        *created_lines,
    ]
    return "\n".join(lines)


def render_ambiguous_clarification(resource_trace: object, project_name: str | None = None) -> str:
    data = resource_trace.to_dict() if hasattr(resource_trace, "to_dict") else dict(resource_trace)
    selected = data.get("selected_resource", {})
    if isinstance(selected, dict):
        path = selected.get("path", "")
        resource_type = selected.get("type", "")
    else:
        path = str(selected)
        resource_type = ""
    lines = [
        "Commande comprise partiellement :",
        "",
        f"- ressource détectée : {path or 'aucune'}",
        f"- type : {resource_type or 'inconnu'}",
        f"- statut : {data.get('intake_status', 'ambiguous')}",
        "",
        "Reformule par exemple :",
        "",
        f"analyse le projet {path}" if path else "analyse le projet <chemin>",
    ]
    if project_name:
        lines.insert(2, f"- projet identifié : {project_name}")
    return render_slypilot_message("SlyPilot", lines)


def render_error_message(title: str, reason: str, path: str | None = None) -> str:
    lines = [title, "", reason]
    if path:
        lines.extend(["", "Chemin :", "", path])
    return render_slypilot_message("SlyPilot", lines)


def render_technical_request_prompt() -> str:
    return render_slypilot_message(
        "SlyPilot",
        [
            "SlyPilot attend une tâche technique.",
            "",
            "Exemples :",
            "- analyse architecture SlyPilot",
            "- corrige bug upload SlyScan",
            "- explique problème login Hermes",
        ],
    )


def render_response_block(project_name: str, status_line: str, action_line: str) -> str:
    return render_slypilot_message(
        "SlyPilot",
        [
            f"Projet détecté :",
            project_name,
            "",
            "Statut :",
            status_line,
            "",
            "Action recommandée :",
            "",
            action_line,
        ],
    )


def render_verbose_traces(resource_trace: object, coordinator_trace: object) -> str:
    return "\n\n".join(
        [
            render_resource_trace(resource_trace),
            render_coordinator_trace(coordinator_trace),
        ]
    )


def render_packet_summary(metadata: dict[str, object]) -> str:
    def _fmt(value: object) -> str:
        if isinstance(value, bool):
            return str(value).lower()
        if value is None:
            return "none"
        return str(value)

    lines = [
        hr(),
        "📦 PACKET SUMMARY",
        hr(),
        "",
        f"project_yaml_loaded: {_fmt(metadata.get('project_yaml_loaded', False))}",
        f"project_yaml_path: {_fmt(metadata.get('project_yaml_path', ''))}",
        f"project_contract_injected: {_fmt(metadata.get('project_contract_injected', False))}",
        f"selected_files_count: {metadata.get('selected_files_count', 0)}",
        f"selected_lines_count: {metadata.get('selected_lines_count', 0)}",
        f"context_reduction_ratio: {_fmt(metadata.get('context_reduction_ratio', None))}",
        f"selected_maps: {', '.join(metadata.get('selected_maps', [])) or 'none'}",
    ]
    return dim("\n".join(lines))
