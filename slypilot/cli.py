"""Command-line entry point for SlyPilot."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from slypilot.adapters.deepseek_adapter import DeepSeekAdapterError, run_deepseek_live
from slypilot.coordinator import coordinate_request
from slypilot.archiops_init import initialize_project
from slypilot.intake import build_intake
from slypilot.runtime import ConversationLoop
from slypilot.runtime.session_registry import SessionRegistry
from slypilot.runtime.session_resume import resume_last_session, resume_session
from slypilot.runtime.session_retention import prune_sessions
from slypilot.ui import (
    render_ambiguous_clarification,
    render_banner,
    render_error_message,
    render_init_message,
    render_packet_summary,
    render_slypilot_message,
    render_coordinator_trace,
    render_resource_trace,
    render_greeting_prompt,
    render_init_required_prompt,
    render_archiops_explanation,
    render_ambiguity_prompt,
    render_path_missing,
    render_sensitive_path,
)
from slypilot.task_packet_builder import append_history


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _print_warnings(warnings: list[str]) -> None:
    if not warnings:
        return
    print()
    print("Avertissements :")
    for warning in warnings:
        print(f"- {warning}")


def _render_sessions_list(repository_root: Path) -> str:
    registry = SessionRegistry(repository_root)
    sessions = registry.list_sessions()
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "📚 Sessions",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
    ]
    if not sessions:
        lines.append("Aucune session enregistrée.")
        return "\n".join(lines)
    for index, session in enumerate(sessions, start=1):
        last_activity = str(session.get("last_activity", ""))[:16].replace("T", " ")
        lines.extend(
            [
                f"{index}. {session.get('session_id', '')}",
                f"   Projet : {session.get('project', 'unknown')}",
                f"   Messages : {session.get('message_count', 0)}",
                f"   Dernière activité : {last_activity[-5:] if last_activity else 'inconnue'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _render_session_state(repository_root: Path) -> str:
    registry = SessionRegistry(repository_root)
    session = registry.latest_session()
    if session is None:
        return "Aucune session disponible."
    lines = [
        "session_id:",
        f"{session.get('session_id', '')}",
        "created_at:",
        f"{session.get('created_at', '')}",
        "cwd:",
        f"{session.get('cwd', '')}",
        "project:",
        f"{session.get('project', '')}",
        "status:",
        f"{session.get('status', '')}",
        "message_count:",
        f"{session.get('message_count', 0)}",
        "last_activity:",
        f"{session.get('last_activity', '')}",
        "pending_action:",
        f"{session.get('pending_action', None)}",
    ]
    return "\n".join(lines)


def _render_history(repository_root: Path, project: str | None = None) -> str:
    registry = SessionRegistry(repository_root)
    sessions = registry.list_sessions()
    if project:
        sessions = [item for item in sessions if str(item.get("project", "")).lower() == project.lower()]
        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"📜 Historique projet : {project.capitalize()}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
        ]
    else:
        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "📜 Historique récent",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
        ]
    if not sessions:
        lines.append("Aucune session disponible.")
        return "\n".join(lines)
    for session in sessions[:10]:
        last_activity = str(session.get("last_activity", ""))[:10]
        lines.append(f"{last_activity[8:10]}/{last_activity[5:7]} {last_activity[11:16] if len(last_activity) >= 16 else '??:??'} - {session.get('project', 'unknown').capitalize()}")
    if project:
        lines.append("")
        lines.append(f"- Session {sessions[0].get('session_id', '')}")
    return "\n".join(lines)


def _handle_session_command(repository_root: Path, args: list[str]) -> int:
    print(_render_session_state(repository_root))
    return 0


def _handle_sessions_command(repository_root: Path) -> int:
    prune_sessions(repository_root)
    print(_render_sessions_list(repository_root))
    return 0


def _handle_history_command(repository_root: Path, args: list[str]) -> int:
    project = args[0] if args else None
    print(_render_history(repository_root, project=project))
    return 0


def _handle_resume_command(repository_root: Path, args: list[str]) -> int:
    if not args:
        raise SystemExit("resume requires a session id or 'last'")
    data = resume_last_session(repository_root) if args[0] == "last" else resume_session(repository_root, args[0])
    session = data["session"]
    print("Session restaurée.")
    print()
    print("Projet :")
    print(f"{session.get('project', 'unknown').capitalize()}")
    print()
    print("Dernière action :")
    events = data["events"]
    assistant_events = [event for event in events if event.get("role") == "assistant"]
    if assistant_events:
        print(assistant_events[-1].get("content", "Aucune action"))
    else:
        print("Aucune action")
    return ConversationLoop.from_session_data(repository_root, Path.cwd(), session, events).run()


def main(argv: list[str] | None = None) -> int:
    raw_args = list(argv if argv is not None else sys.argv[1:])
    root = _repo_root()
    interactive_verbose = "--verbose" in raw_args or "--debug" in raw_args
    if raw_args:
        head = raw_args[0]
        if head == "sessions":
            return _handle_sessions_command(root)
        if head == "session":
            return _handle_session_command(root, raw_args[1:])
        if head == "history":
            return _handle_history_command(root, raw_args[1:])
        if head == "resume":
            return _handle_resume_command(root, raw_args[1:])
    if raw_args and raw_args[0] == "init":
        root = Path.cwd()
        result = initialize_project(root)
        print(render_init_message(result.project_name, [str(path.relative_to(root)) for path in result.created_files]))
        print()
        print("Mis à jour :")
        print(f"- {result.updated_index.relative_to(_repo_root())}")
        if result.warnings:
            print()
            print("Avertissements :")
            for warning in result.warnings:
                print(f"- {warning}")
        return 0

    parser = argparse.ArgumentParser(prog="slypilot")
    parser.add_argument("request", nargs="?", help="raw user request to classify")
    parser.add_argument("--dry-run", action="store_true", help="print the initial detection result")
    parser.add_argument("--live-run", action="store_true", help="send the generated packet to the provider")
    parser.add_argument("--verbose", action="store_true", help="show technical traces")
    parser.add_argument("--debug", action="store_true", help="show technical traces")
    args = parser.parse_args(raw_args)

    if not args.request:
        if sys.stdin.isatty():
            return ConversationLoop.start(root, Path.cwd(), verbose=interactive_verbose)
        else:
            request = sys.stdin.read().strip()
            if not request:
                parser.error("a request is required")
            args.request = request

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
    verbose_mode = getattr(args, "verbose", False) or getattr(args, "debug", False)

    if classification.task_type == "unknown":
        print(render_greeting_prompt())
        return 0

    if not coordinated.decision.allowed:
        selected_resource = coordinated.resource.selected_resource or {}
        selected_path = selected_resource.get("path", "") if isinstance(selected_resource, dict) else ""
        selected_type = selected_resource.get("type", "") if isinstance(selected_resource, dict) else ""
        if coordinated.resource.intake_status == "blocked":
            print(render_sensitive_path(selected_path or ""))
        elif coordinated.resource.intake_status == "missing_path":
            print(render_path_missing(coordinated.resource.detected_paths[0] if coordinated.resource.detected_paths else ""))
        elif selected_path and selected_type == "project_directory":
            print(render_ambiguity_prompt(selected_path.split("/")[-1], selected_path))
        else:
            print(render_ambiguity_prompt(project.name if project.name != "unknown" else "Projet", selected_path or project.name))
        if verbose_mode:
            print()
            print(render_resource_trace(coordinated.resource))
            print()
            print(render_coordinator_trace(coordinated.trace))
        return 1

    if args.dry_run:
        packet = coordinated.packet
        assert packet is not None
        append_history(
            root / "slypilot" / "storage" / "history.jsonl",
            packet,
            prompt=intake.raw_request,
        )
        print(render_slypilot_message("Mode brouillon", [f"Projet détecté : {project.name}", f"Statut : {coordinated.resource.intake_status}", f"Action recommandée :", f"- Packet généré : {packet.packet_path.relative_to(root)}"]))
        _print_warnings(packet.warnings)
        if verbose_mode:
            print()
            print(render_resource_trace(coordinated.resource))
            print()
            print(render_coordinator_trace(coordinated.trace))
            print()
            print(render_packet_summary(packet.metadata))
        else:
            print()
            print("Actions recommandées :")
            print(f"- Packet généré : {packet.packet_path.relative_to(root)}")
    elif args.live_run:
        packet = coordinated.packet
        assert packet is not None
        print(render_slypilot_message("Mode exécution", [f"Projet détecté : {project.name}", f"Statut : {coordinated.resource.intake_status}", f"Action recommandée :", f"- Packet prêt : {packet.packet_path.relative_to(root)}"]))
        _print_warnings(packet.warnings)
        if verbose_mode:
            print()
            print(render_resource_trace(coordinated.resource))
            print()
            print(render_coordinator_trace(coordinated.trace))
            print()
            print(render_packet_summary(packet.metadata))
        try:
            response = run_deepseek_live(packet)
        except DeepSeekAdapterError as exc:
            print()
            print("Erreur fournisseur :")
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
        print()
        print("Réponse fournisseur :")
        print(response.response_text)
        print()
        print("Métriques :")
        print(f"- provider: {response.provider}")
        print(f"- model: {response.model}")
        print(f"- response_tokens: {response.response_tokens}")
    else:
        print(render_slypilot_message("Résumé", [f"Projet détecté : {project.name}", f"Type de tâche : {classification.task_type}", "Mode : interactif"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
