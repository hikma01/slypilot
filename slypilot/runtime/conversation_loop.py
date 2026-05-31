"""Interactive conversation loop for SlyPilot."""

from __future__ import annotations

from pathlib import Path
from typing import Callable
from datetime import datetime, timezone

from slypilot.coordinator import coordinate_request
from slypilot.intake import build_intake
from slypilot.project import prepare_project
from slypilot.ui import (
    render_banner,
    render_resource_trace,
    render_coordinator_trace,
    render_slypilot_message,
    render_greeting_prompt,
    render_init_required_prompt,
    render_init_confirmation,
    render_archiops_explanation,
    render_ambiguity_prompt,
    render_cancel_action,
    render_execution_stage,
    render_analysis_restitution,
    render_final_failure,
    render_info_followup,
    render_path_missing,
    render_sensitive_path,
    render_packet_summary,
    TimelineRenderer,
)

from .session_context import SessionContext
from .session_manager import SessionManager
from .session_registry import SessionRegistry, SessionSummary
from .session_store import SessionStore
from .pending_action_executor import PendingActionExecutor
from .execution_events import EventStatus
from .execution_timeline import ExecutionTimeline


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def selected_project_label(resource: object, fallback: str) -> str:
    selected = getattr(resource, "selected_resource", None)
    if isinstance(selected, dict):
        path = str(selected.get("path", ""))
        if path:
            return Path(path).name
    if fallback:
        return fallback
    return "Projet"


class ConversationLoop:
    def __init__(
        self,
        repository_root: Path,
        cwd: Path,
        input_func: Callable[[str], str] = input,
        output_func: Callable[[str], None] = print,
        shell: str | None = None,
        user: str | None = None,
        verbose: bool = False,
    ) -> None:
        self.repository_root = repository_root
        self.cwd = cwd
        self.input = input_func
        self.output = output_func
        self.verbose = verbose
        self.session_manager = SessionManager(cwd=cwd, shell=shell, user=user)
        self.session = self.session_manager.context
        self.store = SessionStore(repository_root / "runtime" / "sessions")
        self.registry = SessionRegistry(repository_root)
        self.pending_action: dict[str, object] | None = None
        self.pending_executor = PendingActionExecutor()
        self.timeline_renderer = TimelineRenderer(output_func=self.output)

        def _on_timeline_event(event: "ExecutionEvent") -> None:
            self.timeline_renderer.render_event(event)
            self._log_event("system", "execution_event", **event.to_dict())

        self.timeline = ExecutionTimeline(on_event=_on_timeline_event)

    @classmethod
    def start(cls, repository_root: Path, cwd: Path, verbose: bool = False) -> int:
        return cls(repository_root, cwd, verbose=verbose).run()

    @classmethod
    def from_session_data(
        cls,
        repository_root: Path,
        cwd: Path,
        session_data: dict[str, object],
        events: list[dict[str, object]],
        verbose: bool = False,
    ) -> "ConversationLoop":
        loop = cls(repository_root, cwd, verbose=verbose)
        session_id = str(session_data.get("session_id", loop.session.session_id))
        started_at = str(session_data.get("created_at", loop.session.started_at))
        loop.session = SessionContext(
            session_id=session_id,
            started_at=started_at,
            cwd=str(session_data.get("cwd", loop.session.cwd)),
            user=loop.session.user,
            shell=loop.session.shell,
            status=str(session_data.get("status", "active")),
            last_user_message="",
            last_assistant_message="",
            last_detected_resource=None,
            last_project={
                "requested_project": session_data.get("project", "unknown"),
                "resolved_project": session_data.get("project", "unknown"),
                "resolution_source": "resume",
            },
            last_decision=None,
            pending_action=session_data.get("pending_action"),
        )
        loop.session_manager._context = loop.session  # type: ignore[attr-defined]
        loop.pending_action = session_data.get("pending_action") if isinstance(session_data.get("pending_action"), dict) else None
        loop.store.append(
            loop.session.session_id,
            {
                "role": "system",
                "event": "session_restored",
                "session_id": loop.session.session_id,
                "timestamp": _now(),
                "message_count": len(events),
            },
        )
        loop._sync_registry(status=str(session_data.get("status", "active")))
        return loop

    def run(self) -> int:
        self._emit_banner()
        self._log_event("system", "session_started", session_id=self.session.session_id)
        self._sync_registry(status="active")
        while True:
            try:
                raw = self.input("👤 Vous\n> ").strip()
            except KeyboardInterrupt:
                self._close_session()
                self._emit_goodbye("Session fermée.")
                return 0
            except EOFError:
                self._close_session()
                self._emit_goodbye("Session fermée.")
                return 0

            if not raw:
                continue

            lowered = raw.lower()
            if lowered in {"exit", "quit", "q"}:
                self._close_session()
                self._emit_goodbye("Session fermée.")
                return 0
            if lowered == "help":
                self._emit_help()
                continue
            if lowered == "session":
                self._emit_session_state()
                continue
            if lowered == "clear":
                self._clear_screen()
                continue

            if self.pending_action is not None:
                handled = self._handle_pending_reply(raw)
                if handled:
                    continue

            self._handle_message(raw)

    def _emit_banner(self) -> None:
        self.output(render_banner())
        self.output("")
        self.output(f"Session : {self.session.session_id}")
        self.output("")
        self.output("Assistant de coordination technique.")
        self.output("")
        self.output("Tape ta demande.")
        self.output("Pour quitter : exit, quit ou Ctrl+C.")

    def _log_event(self, role: str, event: str, **payload: object) -> None:
        self.store.append(
            self.session.session_id,
            {
                "role": role,
                "event": event,
                "session_id": self.session.session_id,
                "timestamp": _now(),
                **payload,
            },
        )

    def _emit_goodbye(self, message: str) -> None:
        self.output("")
        self.output(message)

    def _clear_screen(self) -> None:
        self.output("\033[2J\033[H")

    def _emit_help(self) -> None:
        self.output(
            "\n".join(
                [
                    "Exemples :",
                    "- analyse le projet /Users/.../MonProjet",
                    "- initialise ARCHI OPS pour ce projet",
                    "- affiche l’état du projet",
                    "- explique le dernier blocage",
                ]
            )
        )

    def _emit_session_state(self) -> None:
        self.output(
            "\n".join(
                [
                    f"session_id: {self.session.session_id}",
                    f"cwd: {self.session.cwd}",
                    f"last_project: {self.session.last_project}",
                    f"last_resource: {self.session.last_detected_resource}",
                    f"last_decision: {self.session.last_decision}",
                    f"pending_action: {self.pending_action}",
                ]
            )
        )

    def _emit_debug_traces(self, coordinated: object, packet_metadata: dict[str, object] | None = None) -> None:
        if not self.verbose:
            return
        self.output("")
        self.timeline.emit("RESOURCE_TRACE", "RESOURCE_TRACE", status=EventStatus.SUCCESS)
        self.output(render_resource_trace(coordinated.resource))
        self.output("")
        self.timeline.emit("COORDINATOR_TRACE", "COORDINATOR_TRACE", status=EventStatus.SUCCESS)
        self.output(render_coordinator_trace(coordinated.trace))
        if packet_metadata is not None:
            self.output("")
            self.timeline.emit("PACKET_SUMMARY", "PACKET_SUMMARY", status=EventStatus.SUCCESS)
            self.output(render_packet_summary(packet_metadata))

    def _should_run_expert_flow(self, coordinated: object) -> bool:
        trace_obj = getattr(coordinated, "trace", None)
        if trace_obj is None:
            return False
        if hasattr(trace_obj, "to_dict"):
            intent_trace = trace_obj.to_dict().get("intent_trace")
        else:
            intent_trace = getattr(trace_obj, "intent_trace", None)
        if not isinstance(intent_trace, dict):
            return False
        return intent_trace.get("final_decision") == "auto_prepare_then_analyze"

    def _handle_pending_reply(self, raw: str) -> bool:
        execution = self.pending_executor.resolve(raw, self.pending_action)
        if not execution.handled:
            return False

        pending_type = str(self.pending_action.get("type", "")) if self.pending_action else ""
        normalized = execution.normalized_response

        if pending_type in {"init_required", "init_archiops", "choose_next_action"}:
            if execution.action == "info":
                project_name = str(self.pending_action.get("project", self.pending_action.get("project_name", "ce projet")))
                self.output(
                    render_archiops_explanation(project_name)
                )
                self.output("")
                self.output(render_info_followup())
                self._append_user(raw)
                self._append_assistant("ARCHI OPS expliqué.")
                return True
            if execution.action == "prepare_project":
                project_name = str(self.pending_action.get("target", self.pending_action.get("project_name", "")))
                project_path = str(self.pending_action.get("project_path", self.session.cwd))
                self.timeline.emit("PROJECT_PREPARATION_STARTED", "Vérification de la préparation", status=EventStatus.RUNNING)
                preparation = prepare_project(project_path)
                if preparation.preparation_status == "failed":
                    reason = preparation.errors[0] if preparation.errors else "préparation impossible"
                    self.timeline.emit("PROJECT_PREPARATION_COMPLETED", "Préparation du projet", status=EventStatus.FAILED, details=reason)
                    self.output(
                        render_slypilot_message(
                            "Je n'ai pas pu préparer le projet.",
                            [
                                f"Projet détecté : {project_name}",
                                f"Chemin : {project_path}",
                                "",
                                "Raison :",
                                reason,
                                "",
                                "Action recommandée :",
                                "vérifie le chemin ou les droits d'accès.",
                            ],
                        )
                    )
                    self._append_user(raw)
                    self._append_assistant("préparation du projet impossible.")
                    self.pending_action = None
                    self.session = self.session_manager.update(pending_action=None)
                    self._sync_registry(status="active")
                    return True
                self.timeline.emit("PROJECT_PREPARATION_COMPLETED", "Préparation terminée", status=EventStatus.SUCCESS)
                self.output(
                    render_slypilot_message(
                        "Préparation du projet terminée.",
                        [
                            f"Projet détecté : {project_name}",
                            "",
                            "Préparation du diagnostic initial...",
                        ],
                    )
                )
                self.timeline.emit("DIAGNOSTIC_STARTED", "Préparation du diagnostic initial", status=EventStatus.RUNNING)
                self._append_user(raw)
                self._append_assistant(f"préparation du projet terminée pour {project_name}.")
                self.pending_action = None
                self.session = self.session_manager.update(pending_action=None)
                self._sync_registry(status="active")
                self._run_followup_analysis(project_name, project_path, raw)
                return True
            if execution.action == "cancel":
                self.output(render_cancel_action())
                self._append_user(raw)
                self._append_assistant("je n’initialise pas ARCHI OPS pour le projet courant.")
                self.pending_action = None
                self.session = self.session_manager.update(pending_action=None)
                self._sync_registry(status="active")
                return True
        if pending_type in {"clarification", "choose_next_action"}:
            if execution.action == "info":
                target = str(self.pending_action.get("project", self.pending_action.get("project_name", "ce projet")))
                self.output(render_archiops_explanation(target))
                self.output("")
                self.output(render_info_followup())
                self._append_user(raw)
                self._append_assistant("ARCHI OPS expliqué.")
                return True
            if execution.action in {"analyze_project", "minimal_project_scan", "cancel"}:
                target = str(self.pending_action.get("target", self.pending_action.get("project_name", "")))
                if execution.action == "analyze_project":
                    self.output(render_slypilot_message("Action sélectionnée :", [f"Analyser le projet pour {target}."]))
                    project_path = str(self.pending_action.get("project_path", self.cwd))
                    self._append_user(raw)
                    self._append_assistant(f"analyser le projet pour {target}.")
                    self.pending_action = None
                    self.session = self.session_manager.update(pending_action=None)
                    self._sync_registry(status="active")
                    self._run_followup_analysis(target, project_path, raw)
                    return True
                if execution.action == "minimal_project_scan":
                    self.output(render_slypilot_message("Action sélectionnée :", [f"Analyse minimale immédiate pour {target}."]))
                    self._append_user(raw)
                    self._append_assistant(f"analyse minimale immédiate pour {target}.")
                    self.pending_action = None
                    self.session = self.session_manager.update(pending_action=None)
                    self._sync_registry(status="active")
                    return True
                if execution.action == "cancel":
                    self.output(render_cancel_action())
                    self._append_user(raw)
                    self._append_assistant("demande annulée.")
                    self.pending_action = None
                    self.session = self.session_manager.update(pending_action=None)
                    self._sync_registry(status="active")
                    return True
        return False

    def _handle_message(self, raw: str) -> None:
        self.timeline.emit("PROJECT_DETECTED", "Détection du projet", status=EventStatus.RUNNING)
        intake = build_intake(raw, self.repository_root)
        coordinated = coordinate_request(
            intake,
            self.repository_root,
            current_working_directory=self.cwd,
            dry_run=True,
            live_run=False,
        )
        project = coordinated.project
        resource = coordinated.resource

        if project.name not in {"unknown", "none"}:
            self.timeline.emit("PROJECT_DETECTED", "Projet détecté", status=EventStatus.SUCCESS, details=project.name)
        else:
            self.timeline.emit("PROJECT_DETECTED", "Détection du projet", status=EventStatus.FAILED, details="Projet inconnu")

        self.session = self.session_manager.update(
            last_user_message=raw,
            last_detected_resource=resource.to_dict(),
            last_project={
                "requested_project": project.requested_project,
                "resolved_project": project.name,
                "resolution_source": project.resolution_source,
                "project_path": str(self.cwd),
                "archiops_status": "present" if (self.cwd / "Documents" / "ARCHIOPS" / "project.yaml").exists() else "missing",
            },
            last_decision={
                "action": coordinated.decision.allowed,
                "reason": coordinated.decision.reason,
            },
        )
        self._append_user(raw)

        if coordinated.intent.classification.task_type == "unknown":
            message = render_greeting_prompt()
            self.output(message)
            self._append_assistant("Bonjour. Je peux t'aider à analyser un projet.")
            self._emit_debug_traces(coordinated)
            self._sync_registry(status="active")
            return

        if self._should_run_expert_flow(coordinated) and project.name not in {"unknown", "none"}:
            project_label = selected_project_label(resource, project.name)
            selected_resource = resource.selected_resource or {}
            project_path = str(selected_resource.get("path", self.cwd)) if isinstance(selected_resource, dict) else self.cwd.as_posix()
            if self._is_analysis_request(raw):
                preparation = None
                if resource.intake_status == "init_required":
                    self.output(
                        render_slypilot_message(
                            f"Projet détecté : {project_label}",
                            [
                                f"Chemin : {project_path}",
                                "",
                                "Je vais préparer le projet pour pouvoir l’analyser correctement.",
                            ],
                        )
                    )
                    self.output(render_execution_stage("Préparation du projet", "en cours"))
                    self.output(render_execution_stage("Cartographie", "en cours"))
                    self.output(render_execution_stage("Construction du contexte", "en cours"))
                    self.output(render_execution_stage("Analyse", "en cours"))
                    self.output(render_execution_stage("Restitution", "en cours"))
                    self.timeline.emit("PROJECT_PREPARATION_STARTED", "Vérification de la préparation", status=EventStatus.RUNNING)
                    preparation = prepare_project(project_path)
                    if preparation.preparation_status == "failed":
                        reason = preparation.errors[0] if preparation.errors else "préparation impossible"
                        self.output(render_execution_stage("Préparation du projet", "échec", reason))
                        self.timeline.emit("PROJECT_PREPARATION_COMPLETED", "Préparation du projet", status=EventStatus.FAILED, details=reason)
                        self.output(render_final_failure(project_label, reason, "Vérifie le chemin ou les droits d’accès."))
                        self._append_assistant("préparation du projet impossible.")
                        self._sync_registry(status="active")
                        return
                    self.output(render_execution_stage("Préparation du projet", "terminé"))
                    self.output(render_execution_stage("Cartographie", "terminé"))
                    self.output(render_execution_stage("Construction du contexte", "terminé"))
                    self.output(render_execution_stage("Analyse", "terminé"))
                    self.output(render_execution_stage("Restitution", "terminé"))
                    self.timeline.emit("PROJECT_PREPARATION_COMPLETED", "Préparation terminée", status=EventStatus.SUCCESS)
                    self._append_assistant(f"préparation du projet terminée pour {project_label}.")
                else:
                    self.timeline.emit("PROJECT_PREPARATION_STARTED", "Vérification de la préparation", status=EventStatus.RUNNING)
                    self.timeline.emit("PROJECT_PREPARATION_COMPLETED", "Préparation déjà disponible", status=EventStatus.SUCCESS)
                    self.output(
                        render_slypilot_message(
                            f"Projet détecté : {project_label}",
                            [
                                f"Chemin : {project_path}",
                                "",
                                "Préparation déjà disponible.",
                            ],
                        )
                    )
                    self.output(
                        render_slypilot_message(
                            "Préparation du diagnostic initial...",
                            [
                                "Diagnostic initial basé sur la cartographie locale et le contexte borné.",
                            ],
                        )
                    )
                    self._append_assistant(f"préparation déjà disponible pour {project_label}.")

                if preparation is not None and preparation.preparation_status == "success":
                    self.session = self.session_manager.update(
                        last_project={
                            "requested_project": project_label,
                            "resolved_project": project_label,
                            "resolution_source": "explicit_path",
                            "project_path": project_path,
                            "archiops_status": "present",
                        },
                    )

                self.timeline.emit("CARTOGRAPHY_LOADING", "Chargement de la cartographie", status=EventStatus.RUNNING)
                self.timeline.emit("CONTEXT_BUILDING", "Construction du contexte", status=EventStatus.RUNNING)
                self.timeline.emit("DIAGNOSTIC_STARTED", "Préparation du diagnostic initial", status=EventStatus.RUNNING)

                followup = coordinate_request(
                    build_intake(raw, self.repository_root),
                    self.repository_root,
                    current_working_directory=self.cwd,
                    dry_run=True,
                    live_run=False,
                )
                if followup.decision.allowed and followup.packet is not None:
                    map_count = followup.packet.metadata.get("selected_maps_count", 0)
                    line_count = followup.packet.metadata.get("selected_lines_count", 0)

                    self.timeline.emit("CARTOGRAPHY_LOADED", f"{map_count} cartes chargées", status=EventStatus.SUCCESS)
                    self.timeline.emit("CONTEXT_READY", f"{line_count} lignes sélectionnées", status=EventStatus.SUCCESS)
                    self.timeline.emit("DIAGNOSTIC_COMPLETED", "Diagnostic généré", status=EventStatus.SUCCESS)

                    try:
                        packet_rel_path = followup.packet.packet_path.relative_to(self.repository_root)
                    except ValueError:
                        packet_rel_path = followup.packet.packet_path
                    self.output("")
                    self.output(
                        render_slypilot_message(
                            "Préparation du diagnostic initial...",
                            [
                                "Diagnostic initial basé sur la cartographie locale et le contexte borné.",
                            ],
                        )
                    )
                    self.output(
                        render_analysis_restitution(
                            project_label,
                            followup.packet.metadata,
                            str(packet_rel_path),
                        )
                    )
                    self._append_assistant(f"diagnostic initial prêt pour {project_label}.")
                else:
                    reason = followup.block_reason or followup.decision.reason or "analyse impossible"
                    self.timeline.emit("DIAGNOSTIC_COMPLETED", "Préparation du diagnostic initial", status=EventStatus.FAILED, details=reason)
                    self.output(render_final_failure(project_label, reason, "Vérifie le projet ou reformule la demande."))
                    self._append_assistant(f"analyse impossible pour {project_label}: {reason}")
                self._emit_debug_traces(followup)
                self._sync_registry(status="active")
                return
            self.pending_action = {
                "id": f"{self.session.session_id}:choose_next_action",
                "type": "choose_next_action",
                "project_name": project_label,
                "project_path": project_path,
                "status": "waiting_user_choice",
                "options": {
                    "1": {
                        "action": "analyze_project",
                        "requires_preparation": True,
                        "next_steps": ["prepare_project", "analyze_project"],
                    },
                    "2": {
                        "action": "minimal_project_scan",
                        "requires_preparation": False,
                    },
                    "3": {
                        "action": "cancel",
                        "requires_preparation": False,
                    },
                    "i": {
                        "action": "explain_preparation",
                        "keep_pending_action": True,
                    },
                },
                "allowed_responses": ["1", "2", "3", "i", "info"],
                "requires_confirmation": True,
            }
            self.session = self.session_manager.update(pending_action=self.pending_action)
            self.output(
                render_slypilot_message(
                    f"Projet détecté : {project_label}",
                    [
                        f"Chemin : {project_path}",
                        "",
                        "Que veux-tu faire ?",
                        "",
                        "[1] Analyser le projet",
                        "[2] Afficher l’état du projet",
                        "[3] Annuler",
                    ],
                )
            )
            self._append_assistant("Choix d'action demandé pour le projet détecté.")
            return

        if not coordinated.decision.allowed:
            selected_resource = resource.selected_resource or {}
            selected_path = selected_resource.get("path", "") if isinstance(selected_resource, dict) else ""
            selected_type = selected_resource.get("type", "") if isinstance(selected_resource, dict) else ""
            if resource.intake_status == "blocked":
                message = render_sensitive_path(selected_path or "")
            elif resource.intake_status == "missing_path":
                message = render_path_missing(resource.detected_paths[0] if resource.detected_paths else "")
            elif selected_path and selected_type == "project_directory":
                project_label = selected_project_label(resource, selected_path.split("/")[-1])
                self.pending_action = {
                    "type": "choose_next_action",
                    "project_name": project_label,
                    "project_path": selected_path,
                    "status": "waiting_user_choice",
                    "options": {
                        "1": {
                            "action": "analyze_project",
                            "requires_preparation": True,
                            "next_steps": ["prepare_project", "analyze_project"],
                        },
                        "2": {
                            "action": "minimal_project_scan",
                            "requires_preparation": False,
                        },
                        "3": {
                            "action": "cancel",
                            "requires_preparation": False,
                        },
                    },
                    "allowed_responses": ["1", "2", "3"],
                    "requires_confirmation": True,
                }
                self.session = self.session_manager.update(pending_action=self.pending_action)
                message = render_ambiguity_prompt(project_label, selected_path)
            else:
                message = render_slypilot_message(
                    "Demande ambiguë.",
                    [
                        "Veuillez reformuler votre demande.",
                    ],
                )
            self.output(message)
            self._append_assistant(message)
            self._emit_debug_traces(coordinated)
            self._sync_registry(status="active")
            return

        packet = coordinated.packet
        assert packet is not None
        try:
            packet_rel_path = packet.packet_path.relative_to(self.repository_root)
        except ValueError:
            packet_rel_path = packet.packet_path
        response_lines = [
            f"Projet détecté : {project.name}",
            f"Statut : {resource.intake_status}",
            "Action recommandée :",
            f"- Packet généré : {packet_rel_path}",
        ]
        self.output(render_slypilot_message("Mode brouillon", response_lines))
        self._emit_debug_traces(coordinated, packet.metadata)
        self._append_assistant(f"Packet généré : {packet_rel_path}")
        self._sync_registry(status="active")

    def _is_analysis_request(self, raw: str) -> bool:
        normalized = raw.lower()
        return any(
            keyword in normalized
            for keyword in (
                "analyse",
                "analyze",
                "check",
                "vérifie",
                "verifie",
                "inspecte",
                "audite",
                "diagnostique",
                "regarde",
            )
        )

    def _run_followup_analysis(self, project_name: str, project_path: str, raw: str) -> None:
        self.timeline.emit("CARTOGRAPHY_LOADING", "Chargement de la cartographie", status=EventStatus.RUNNING)
        self.timeline.emit("CONTEXT_BUILDING", "Construction du contexte", status=EventStatus.RUNNING)

        followup = coordinate_request(
            build_intake(raw, self.repository_root),
            self.repository_root,
            current_working_directory=Path(project_path),
            dry_run=True,
            live_run=False,
        )
        if followup.decision.allowed and followup.packet is not None:
            map_count = followup.packet.metadata.get("selected_maps_count", 0)
            line_count = followup.packet.metadata.get("selected_lines_count", 0)

            self.timeline.emit("CARTOGRAPHY_LOADED", f"{map_count} cartes chargées", status=EventStatus.SUCCESS)
            self.timeline.emit("CONTEXT_READY", f"{line_count} lignes sélectionnées", status=EventStatus.SUCCESS)
            self.timeline.emit("DIAGNOSTIC_COMPLETED", "Diagnostic généré", status=EventStatus.SUCCESS)

            try:
                packet_rel_path = followup.packet.packet_path.relative_to(self.repository_root)
            except ValueError:
                packet_rel_path = followup.packet.packet_path
            self.output("")
            self.output(
                render_analysis_restitution(
                    project_name,
                    followup.packet.metadata,
                    str(packet_rel_path),
                )
            )
            self._append_assistant(f"diagnostic initial prêt pour {project_name}.")
            return

        reason = followup.block_reason or followup.decision.reason or "analyse impossible"
        self.timeline.emit("DIAGNOSTIC_COMPLETED", "Préparation du diagnostic initial", status=EventStatus.FAILED, details=reason)
        self.output(render_final_failure(project_name, reason, "Vérifie le projet ou reformule la demande."))
        self._append_assistant(f"analyse impossible pour {project_name}: {reason}")

    def _append_user(self, raw: str) -> None:
        self.store.append(
            self.session.session_id,
            {
                "role": "user",
                "content": raw,
                "timestamp": _now(),
            },
        )

    def _append_assistant(self, content: str) -> None:
        self.store.append(
            self.session.session_id,
            {
                "role": "assistant",
                "content": content,
                "timestamp": _now(),
            },
        )

    def _sync_registry(self, status: str) -> None:
        last_project = self.session.last_project if isinstance(self.session.last_project, dict) else {}
        self.registry.upsert_session(
            session_id=self.session.session_id,
            created_at=self.session.started_at,
            last_activity=_now(),
            project=str(last_project.get("resolved_project", "unknown")),
            status=status,
            message_count=self.store.count(self.session.session_id),
            cwd=self.session.cwd,
            pending_action=self.pending_action,
            project_path=str(last_project.get("project_path", self.session.cwd)),
            archiops_status=str(last_project.get("archiops_status", "missing")),
        )

    def _close_session(self) -> None:
        self.session = self.session_manager.update(status="closed")
        last_project = self.session.last_project if isinstance(self.session.last_project, dict) else {}
        summary = SessionSummary(
            session_id=self.session.session_id,
            project=str(last_project.get("resolved_project", "unknown")),
            started_at=self.session.started_at,
            ended_at=_now(),
            message_count=self.store.count(self.session.session_id),
            decisions=[str(self.session.last_decision)] if self.session.last_decision else [],
            incidents=[],
            pending_action=self.pending_action,
        )
        self.registry.save_summary(summary)
        self._sync_registry(status="closed")
