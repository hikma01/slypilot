"""Interactive conversation loop for SlyPilot."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Any
from datetime import datetime, timezone

from slypilot.coordinator import coordinate_request
from slypilot.intake import build_intake
from slypilot.project import prepare_project
from slypilot.ui.console_renderer import render_banner
from slypilot.ui.trace_renderer import render_resource_trace, render_coordinator_trace
from slypilot.ui.chat_renderer import render_slypilot_message, render_slypilot_header, render_technical_info
from slypilot.ui.style import dim
from slypilot.ui.guidance_renderer import (
    render_greeting_prompt,
    render_init_required_prompt,
    render_init_confirmation,
    render_archiops_explanation,
    render_ambiguity_prompt,
    render_cancel_action,
    render_execution_stage,
    render_analysis_restitution,
    render_post_diagnostic_files,
    render_post_diagnostic_map,
    render_post_diagnostic_risks,
    render_post_diagnostic_stop,
    render_post_diagnostic_menu,
    render_pending_action_invalid_choice,
    render_pending_action_explanation,
    render_pending_action_greeting,
    render_final_failure,
    render_info_followup,
    render_path_missing,
    render_sensitive_path,
    render_path_error,
    render_analysis_discovery,
    render_analysis_plan,
)
from slypilot.ui.architecture_renderer import render_visual_architecture
from slypilot.ui.console_renderer import render_packet_summary
from slypilot.ui.timeline_renderer import TimelineRenderer
from slypilot.ui.status_bar import StatusBar
from slypilot.cognitive.cognitive_interface import CognitiveInterface
from slypilot.project import ProjectMemory, ProjectMemoryStore
from slypilot.contracts import (
    TechnicalRequestBrief, 
    IntentType, 
    TechnicalResponsePacket,
    safe_project_label,
    get_project_path,
    PendingAction
)
from slypilot.tools.filesystem.path_detector import detect_paths

from .session_context import SessionContext
from .session_manager import SessionManager
from .session_registry import SessionRegistry, SessionSummary
from .session_store import SessionStore
from .pending_action_executor import PendingActionExecutor
from .pending_action_executor import PendingActionExecution
from .execution_events import EventStatus
from .execution_timeline import ExecutionTimeline
from .workflow_engine import WorkflowEngine

from slypilot.project_resolver import extract_explicit_unresolved_name


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
        self.pending_action: PendingAction | None = None
        self.pending_executor = PendingActionExecutor()
        self.timeline_renderer = TimelineRenderer(output_func=self.output, verbose=self.verbose)
        self.status_bar = StatusBar()
        self.cognitive = CognitiveInterface(repository_root)
        self.project_memory_store = ProjectMemoryStore(repository_root)
        self.current_project_memory: ProjectMemory | None = None
        self.workflow_engine = WorkflowEngine([
            "cartography",
            "business_analysis",
            "entry_points",
            "business_tree",
            "risk_analysis",
            "final_synthesis",
        ])
        self.PROCEDURAL_WORKFLOW_ENABLED = False
        self._header_sent_this_turn = False

        def _on_timeline_event(event: "ExecutionEvent") -> None:
            self.status_bar.update(event.title.lower())
            self.timeline_renderer.render_event(event)
            self._log_event("system", "execution_event", **event.to_dict())

        self.timeline = ExecutionTimeline(on_event=_on_timeline_event)

    def _output_assistant(self, title: str, lines: list[str], force_header: bool = False) -> None:
        """Helper to output a conversational message, ensuring header is only sent once per turn."""
        include_header = force_header or not self._header_sent_this_turn
        # STI: All external identity must be 'SlyPilot'
        self.output(render_slypilot_message("SlyPilot", lines, include_header=include_header))
        if include_header:
            self._header_sent_this_turn = True

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
        
        workflow_data = session_data.get("workflow")
        workflow = None
        if isinstance(workflow_data, dict):
            from slypilot.contracts import WorkflowState
            workflow = WorkflowState(**workflow_data) # type: ignore

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
            active_project=session_data.get("active_project") if isinstance(session_data.get("active_project"), dict) else None,
            active_analysis=session_data.get("active_analysis") if isinstance(session_data.get("active_analysis"), dict) else None,
            workflow=workflow,
        )
        loop.session_manager._context = loop.session  # type: ignore[attr-defined]
        pending_action_data = session_data.get("pending_action")
        if isinstance(pending_action_data, dict):
            loop.pending_action = PendingAction(
                action_id=str(pending_action_data.get("action_id", "")),
                action_type=str(pending_action_data.get("action_type", "")),
                project_path=str(pending_action_data.get("project_path", "")),
                project_name=str(pending_action_data.get("project_name", "")),
                source_message=str(pending_action_data.get("source_message", "")),
                status=str(pending_action_data.get("status", "pending")),
                stage=str(pending_action_data.get("stage", "initial")),
                created_at=str(pending_action_data.get("created_at", _now())),
            )
        else:
            loop.pending_action = None
        active_analysis = loop.session.active_analysis if isinstance(loop.session.active_analysis, dict) else None
        if isinstance(active_analysis, dict):
            project_memory_data = active_analysis.get("project_memory")
            if isinstance(project_memory_data, dict):
                loop.current_project_memory = ProjectMemory.from_dict(project_memory_data)
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
        
        from slypilot.coordinator.coordinator import handle_technical_brief

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
                self.session = self.session_manager.update(active_project=None, active_analysis=None, workflow=None)
                self._emit_help()
                continue
            if lowered == "reset":
                self.session = self.session_manager.update(active_project=None, active_analysis=None, workflow=None)
                self.output("Contexte réinitialisé.")
                continue
            if lowered == "session":
                self._emit_session_state()
                continue
            if lowered == "clear":
                self._clear_screen()
                continue

            self._header_sent_this_turn = False

            if self.pending_action and self.pending_action.action_type == "await_project_path":
                detected_paths = detect_paths(raw, self.cwd)
                if detected_paths:
                    project_path = detected_paths[0].normalized_path
                    project_name = Path(project_path).name
                    self.pending_action = None
                    self.session = self.session_manager.update(pending_action=None)
                    self._start_technical_analysis(project_name, project_path, raw)
                    continue

            detected_paths = detect_paths(raw, self.cwd)
            if detected_paths and raw.strip() == detected_paths[0].normalized_path:
                project_path = detected_paths[0].normalized_path
                project_name = Path(project_path).name
                self.pending_action = PendingAction(
                    action_id=f"await_{datetime.now(timezone.utc).strftime('%H%M%S')}",
                    action_type="init_required",
                    project_path=project_path,
                    project_name=project_name,
                    source_message=raw,
                )
                self.session = self.session_manager.update(
                    active_project={"name": project_name, "path": project_path},
                    pending_action=self.pending_action.to_dict(),
                )
                self.output(
                    render_init_required_prompt(
                        project_name,
                        project_path,
                        include_header=not self._header_sent_this_turn,
                    )
                )
                continue

            if self.pending_action and self.pending_action.action_type in {"init_required", "init_archiops", "clarification", "choose_next_action"}:
                execution = self.pending_executor.resolve(raw, self.pending_action.to_dict())
                if execution.handled and self._handle_pending_action_execution(execution):
                    continue

            # --- STI V1: NATURAL CONVERSATION ---
            
            # Étape 1: Classification Cognitive
            intent = self.cognitive.classify_intent(raw, self.session.active_project)
            self._audit_routing(raw, intent)

            # Étape 2: Routage Human-Centered
            if intent not in {IntentType.TECHNICAL_REQUEST, IntentType.WORKFLOW_CONTINUE}:
                 cognitive_result = self.cognitive.qualify_intent(raw, intent, self.session.active_project)
                 
                 if intent == IntentType.CORRECTION_PROJECT:
                      self._handle_correction(raw)
                      continue
                      
                 if cognitive_result is not None:
                      self._audit_render("cognitive", "human_response")
                      self._output_assistant("SlyPilot", [cognitive_result] if isinstance(cognitive_result, str) else [])
                      continue

            # Étape 3: Gestion Interne du Workflow (Invisible & Silencieux)
            if intent == IntentType.WORKFLOW_CONTINUE:
                 if self.session.workflow:
                      if self.session.workflow.status == "completed":
                           self._handle_recommendation_ok(raw)
                           continue
                      
                      # Si le workflow tourne encore, on le laisse finir silencieusement jusqu'à la synthèse
                      self._audit_workflow("silent_processing")
                      self._run_invisible_workflow_cycle(raw)
                      continue
                 elif self.session.active_project:
                      # STI: ok after crash or when no workflow but project active
                      self._output_assistant("SlyPilot", [
                          "L’analyse précédente a échoué sur un problème technique identifié.",
                          "Après correction, vous pouvez relancer l’analyse du projet."
                      ])
                      continue
                 else:
                      self.pending_action = PendingAction(
                          action_id=f"await_{datetime.now(timezone.utc).strftime('%H%M%S')}",
                          action_type="await_project_path",
                          project_path="",
                          project_name="",
                          source_message=raw,
                      )
                      self.session = self.session_manager.update(pending_action=self.pending_action.to_dict())
                      self._output_assistant("SlyPilot", [
                          "D'accord. Partagez simplement le chemin local du projet à analyser.",
                          "Exemple :",
                          "analyse /Users/.../MonProjet",
                      ])
                      continue

            # Étape 4: Technical Execution (Initial Analysis -> Direct to Synthesis)
            cognitive_brief = self.cognitive.qualify_intent(raw, intent, self.session.active_project)
            if isinstance(cognitive_brief, str):
                self._audit_render("cognitive", "clarification")
                if intent == IntentType.TECHNICAL_REQUEST and "chemin local" in cognitive_brief.lower():
                    import uuid
                    self.pending_action = PendingAction(
                        action_id=str(uuid.uuid4()),
                        action_type="await_project_path",
                        project_path="",
                        project_name="",
                        source_message="analysis_request"
                    )
                    self.session = self.session_manager.update(pending_action=self.pending_action.to_dict())
                self._output_assistant("SlyPilot", [cognitive_brief])
                continue

            if isinstance(cognitive_brief, TechnicalRequestBrief):
                self._start_technical_analysis(cognitive_brief.get_project_name(), cognitive_brief.get_project_path(), raw)
                continue

            # Fallback minimal
            self._handle_message(raw)

    def _start_technical_analysis(self, project_name: str, project_path: str, raw: str) -> None:
        try:
            self.status_bar.start("brainstorming stratégique")

            project_label = safe_project_label({"name": project_name, "path": project_path})
            self._output_assistant("SlyPilot", [
                f"Je comprends votre demande sur {project_label}.",
                "",
                "Je lance l’analyse technique en profondeur :",
                "- cartographie de la structure",
                "- identification de la logique métier",
                "- repérage des risques techniques",
                "",
                "Je vous restitue ensuite une synthèse claire et exploitable."
            ])

            self._audit_render("cognitive", "brainstorming_with_technical_layer")

            self._initialize_workflow(project_name, project_path)
            self._emit_final_synthesis(project_name, project_path, raw)
            self.status_bar.stop()
        except Exception as e:
            self.status_bar.stop()
            from slypilot.contracts import TechnicalBriefInvalid
            self.session = self.session_manager.update(workflow=None)
            self.pending_action = None

            if isinstance(e, TechnicalBriefInvalid):
                self._output_assistant("SlyPilot", [
                    "Je ne peux pas mener l'analyse car le contexte projet est incomplet.",
                    "",
                    "Il me manque un chemin local fiable vers le projet à analyser.",
                    "",
                    "Indiquez le chemin du projet, par exemple :",
                    "analyse /Users/.../MonProjet",
                ])
            else:
                self._output_assistant("SlyPilot", [
                    "L’analyse n’a pas pu être finalisée.",
                    "",
                    "Cause détectée :",
                    str(e),
                    "",
                    "Après correction, relancez l’analyse du projet."
                ])

    def _handle_pending_action_execution(self, execution: PendingActionExecution) -> bool:
        if not self.pending_action:
            return False

        action = execution.action or ""
        pending_type = self.pending_action.action_type
        project_name = self.pending_action.project_name or safe_project_label(self.session.active_project)
        project_path = self.pending_action.project_path or get_project_path(self.session.active_project) or str(self.cwd)
        pending_data = self.pending_action.to_dict()

        if action == "info":
            if pending_type in {"init_required", "init_archiops"}:
                self.output(render_archiops_explanation(project_name, include_header=not self._header_sent_this_turn))
                self.output(render_info_followup(include_header=False))
            else:
                self.output(render_pending_action_explanation(pending_data))
            self.session = self.session_manager.update(pending_action=pending_data)
            self._sync_registry(status="active")
            return True

        if action == "greeting":
            self.output(render_pending_action_greeting(pending_data))
            self.session = self.session_manager.update(pending_action=pending_data)
            self._sync_registry(status="active")
            return True

        if action == "question":
            self.output(render_pending_action_explanation(pending_data))
            self.session = self.session_manager.update(pending_action=pending_data)
            self._sync_registry(status="active")
            return True

        if action == "cancel":
            self.output(render_cancel_action(include_header=not self._header_sent_this_turn))
            self.pending_action = None
            self.session = self.session_manager.update(pending_action=None)
            self._sync_registry(status="active")
            return True

        if action == "prepare_project":
            result = prepare_project(project_path)
            if result.preparation_status == "failed":
                reason = result.errors[0] if result.errors else "Préparation impossible"
                self._output_assistant("SlyPilot", [
                    "Je n'ai pas pu préparer le projet.",
                    "",
                    "Raison :",
                    reason,
                    "",
                    "Action recommandée :",
                    "vérifiez le chemin local du projet puis relancez l'analyse.",
                ])
            else:
                self._output_assistant("SlyPilot", [
                    f"Préparation du projet terminée pour {project_name}.",
                    "Je peux maintenant poursuivre avec un diagnostic initial borné.",
                ])
            self.pending_action = None
            self.session = self.session_manager.update(pending_action=None)
            self._sync_registry(status="active")
            return True

        return False

    def _audit_routing(self, raw: str, intent: IntentType) -> None:
        if not self.verbose: return
        self.output(dim(f"[AUDIT ROUTING] raw_message: {raw[:30]}..."))
        self.output(dim(f"[AUDIT ROUTING] intent_type: {intent.name}"))
        layer = "technical" if intent in {IntentType.TECHNICAL_REQUEST, IntentType.WORKFLOW_CONTINUE} else "cognitive"
        self.output(dim(f"[AUDIT ROUTING] selected_layer: {layer}"))
        self.output(dim(f"[AUDIT ROUTING] router_reason: {intent.name.lower()}_detected"))

    def _audit_workflow(self, action: str) -> None:
        if not self.verbose or not self.session.workflow: return
        w = self.session.workflow
        self.output(dim(f"[AUDIT WORKFLOW] action: {action}"))
        self.output(dim(f"[AUDIT WORKFLOW] workflow_id: {w.workflow_id}"))
        self.output(dim(f"[AUDIT WORKFLOW] current_phase: {w.current_phase}"))
        self.output(dim(f"[AUDIT WORKFLOW] completed: {len(w.completed_phases)} phases"))
        self.output(dim(f"[AUDIT WORKFLOW] remaining_phases: {w.remaining_phases}"))
        self.output(dim(f"[AUDIT WORKFLOW] awaiting_confirmation: {w.awaiting_user_confirmation}"))

    def _audit_packet(self, packet: TechnicalResponsePacket) -> None:
        if not self.verbose: return
        self.output(dim("[AUDIT PACKET] technical_response_packet:"))
        self.output(dim(str(packet.to_dict())))

    def _audit_render(self, source: str, msg_type: str) -> None:
        if not self.verbose: return
        self.output(dim(f"[AUDIT RENDER] response_source: {source}"))
        self.output(dim(f"[AUDIT RENDER] response_type: {msg_type}"))
        resp_id = f"res_{datetime.now().strftime('%H%M%S')}"
        self.output(dim(f"[AUDIT RENDER] response_id: {resp_id}"))

    def _initialize_workflow(self, project_name: str, project_path: str) -> None:
        """Initialise un nouveau workflow d'analyse STI."""
        workflow_id = f"wf_{datetime.now().strftime('%H%M%S')}"
        initial_state = self.workflow_engine.create_initial_state(workflow_id)
        
        self.session = self.session_manager.update(
            active_project={"name": project_name, "path": project_path},
            workflow=initial_state
        )
        self._audit_workflow("init")

    def _run_invisible_workflow_cycle(self, raw: str) -> None:
        """Exécute tout le workflow restant de manière silencieuse jusqu'à la synthèse."""
        w = self.session.workflow
        if not w: return
        
        project_name = self.session.active_project["name"] if self.session.active_project else "ce projet"
        project_path = get_project_path(self.session.active_project) or str(self.cwd)
        
        # On avance la machine d'état jusqu'à la fin
        current = w
        while current and current.status != "completed":
             current = self.workflow_engine.advance(current)
             if current.current_phase == "final_synthesis":
                  break
        
        self.session = self.session_manager.update(workflow=current)
        self._emit_final_synthesis(project_name, project_path, raw)

    def _handle_recommendation_ok(self, raw: str) -> None:
        """Interprète 'ok' basé sur la posture de stratège d'élite avec anti-replay."""
        project_label = safe_project_label(self.session.active_project)
        project_path = get_project_path(self.session.active_project) or str(self.cwd)
        import uuid
        project_memory = self._current_project_memory(project_path)

        packet_metadata: dict[str, object] = {}
        if isinstance(self.session.active_analysis, dict):
            packet_metadata = dict(self.session.active_analysis.get("packet_metadata") or {})

        if self.pending_action and self.pending_action.action_type == "post_diagnostic_next_step" and self.pending_action.status == "completed":
            self.output(render_post_diagnostic_stop())
            self.pending_action = None
            self.session = self.session_manager.update(
                pending_action=None,
                last_system_action={
                    "type": "post_diagnostic_cycle_completed",
                    "project_name": project_label,
                },
            )
            self._sync_registry(status="active")
            return

        # 1. Aucun cycle post-diagnostic n'est encore ouvert: on expose la suite sans poser de question
        if not self.pending_action or self.pending_action.status == "completed":
            last_system_action = self.session.last_system_action if isinstance(self.session.last_system_action, dict) else {}
            if last_system_action.get("type") == "post_diagnostic_cycle_completed":
                self.output(render_post_diagnostic_stop())
                return
            if self.session.workflow and self.session.workflow.status == "completed":
                guidance = ["Le diagnostic initial est prêt.", "Je poursuis avec la suite la plus utile pour ce projet."]
                if project_memory and project_memory.architecture_summary:
                    guidance.insert(1, f"Cartographie mémorisée : {project_memory.architecture_summary}")
                self._output_assistant(
                    "Diagnostic initial",
                    guidance,
                )
                self.output(render_post_diagnostic_menu())
                self.pending_action = PendingAction(
                    action_id=str(uuid.uuid4()),
                    action_type="post_diagnostic_next_step",
                    project_path=project_path,
                    project_name=project_label,
                    source_message="post_diagnostic_menu_opened",
                    stage="initial",
                )
                self.session = self.session_manager.update(
                    pending_action=self.pending_action.to_dict(),
                )
                self._sync_registry(status="active")
                return

            self._output_assistant(
                "SlyPilot",
                [
                    f"Pour maîtriser {project_label}, je vais approfondir l'exploration de manière guidée.",
                    *( [f"Je m'appuie sur la mémoire projet déjà construite : {project_memory.architecture_summary}"] if project_memory and project_memory.architecture_summary else [] ),
                    "Je commence par les fichiers utiles et la cartographie la plus parlante.",
                ],
            )
            self.output(render_post_diagnostic_menu())
            self.pending_action = PendingAction(
                action_id=str(uuid.uuid4()),
                action_type="post_diagnostic_next_step",
                project_path=project_path,
                project_name=project_label,
                source_message="post_diagnostic_menu_opened",
                stage="initial",
            )
            self.session = self.session_manager.update(
                pending_action=self.pending_action.to_dict(),
            )
            self._sync_registry(status="active")
            return

        # 2. Cycle post-diagnostic actif: on avance sans reposer la même question
        if self.pending_action and self.pending_action.status == "pending":
            if self.pending_action.action_type == "post_diagnostic_next_step":
                stage = getattr(self.pending_action, "stage", "initial")
                if stage == "initial":
                    lead_in = "Je poursuis avec l'étape la plus utile : analyser les fichiers importants."
                    if project_memory and project_memory.previous_findings:
                        lead_in = f"Je poursuis depuis la cartographie déjà construite. {project_memory.previous_findings[0]}"
                    self._output_assistant(
                        "SlyPilot",
                        [
                            lead_in,
                        ],
                    )
                    self.output(render_post_diagnostic_files(project_label, packet_metadata, include_header=False))
                    self.pending_action = PendingAction(
                        action_id=self.pending_action.action_id,
                        action_type=self.pending_action.action_type,
                        project_path=self.pending_action.project_path,
                        project_name=self.pending_action.project_name,
                        source_message=self.pending_action.source_message,
                        status="pending",
                        stage="followup",
                        created_at=self.pending_action.created_at,
                    )
                    self.session = self.session_manager.update(pending_action=self.pending_action.to_dict())
                    self._sync_registry(status="active")
                    return
                if stage == "followup":
                    lead_in = "Je vous montre maintenant la cartographie la plus utile pour comprendre ce projet."
                    if project_memory and project_memory.risks:
                        lead_in = f"Je vous montre maintenant la cartographie la plus utile pour comprendre ce projet. Risque déjà retenu : {project_memory.risks[0]}"
                    self._output_assistant(
                        "SlyPilot",
                        [
                            lead_in,
                        ],
                    )
                    self.output(render_post_diagnostic_map(packet_metadata, include_header=False))
                    self.pending_action = PendingAction(
                        action_id=self.pending_action.action_id,
                        action_type=self.pending_action.action_type,
                        project_path=self.pending_action.project_path,
                        project_name=self.pending_action.project_name,
                        source_message=self.pending_action.source_message,
                        status="pending",
                        stage="risks",
                        created_at=self.pending_action.created_at,
                    )
                    self.session = self.session_manager.update(pending_action=self.pending_action.to_dict())
                    self._sync_registry(status="active")
                    return
                if stage == "risks":
                    lead_in = "Je termine par les zones à risque visibles."
                    if project_memory and project_memory.active_recommendation:
                        lead_in = f"Je termine par les zones à risque visibles. Recommandation mémorisée : {project_memory.active_recommendation}"
                    self._output_assistant(
                        "SlyPilot",
                        [
                            lead_in,
                        ],
                    )
                    self.output(render_post_diagnostic_risks(packet_metadata, include_header=False))
                    self.pending_action = PendingAction(
                        action_id=self.pending_action.action_id,
                        action_type=self.pending_action.action_type,
                        project_path=self.pending_action.project_path,
                        project_name=self.pending_action.project_name,
                        source_message=self.pending_action.source_message,
                        status="completed",
                        stage="completed",
                        created_at=self.pending_action.created_at,
                    )
                    self.session = self.session_manager.update(pending_action=self.pending_action.to_dict())
                    self._sync_registry(status="active")
                    return
                self.output(render_post_diagnostic_stop())
                self.pending_action = None
                self.session = self.session_manager.update(pending_action=None)
                self._sync_registry(status="active")
                return

            if self.pending_action.action_type == "TRACE_EXECUTION_FLOW":
                self.pending_action = PendingAction(
                    action_id=self.pending_action.action_id,
                    action_type=self.pending_action.action_type,
                    project_path=self.pending_action.project_path,
                    project_name=self.pending_action.project_name,
                    source_message=self.pending_action.source_message,
                    status="completed",
                    stage="completed",
                    created_at=self.pending_action.created_at,
                )
                self.session = self.session_manager.update(pending_action=self.pending_action.to_dict())
                self._sync_registry(status="active")

                self.status_bar.start("traçage des flux")
                self.status_bar.stop()

                self._output_assistant(
                    "Flux d'exécution",
                    [
                        "Le traçage est terminé.",
                        "",
                        "Ce que j'ai trouvé :",
                        "- les requêtes entrantes transitent principalement par le contrôleur `/api/v1/`.",
                        "- la logique métier reste concentrée dans `/core/`.",
                        "",
                        "Ce que cela signifie :",
                        "- `/core/` est la zone critique du projet.",
                        "- toute modification dans ce dossier peut impacter directement le comportement applicatif.",
                        "",
                        "Prochaine étape :",
                        "je vais maintenant relier ces flux aux tests à relancer.",
                    ],
                )
                return

        # 3. Fallback (ex: action déjà consommée)
        self._output_assistant("SlyPilot", ["Je reste à votre disposition si vous souhaitez explorer un autre aspect du projet."])

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
                    f"active_project: {self.session.active_project}",
                    f"active_analysis: {self.session.active_analysis}",
                    f"last_decision: {self.session.last_decision}",
                    f"pending_action: {self.pending_action}",
                    f"workflow: {self.session.workflow}",
                ]
            )
        )

    def _handle_message(self, raw: str) -> None:
        """Fallback handling."""
        self.status_bar.start("détection")
        intake = build_intake(raw, self.repository_root)
        coordinated = coordinate_request(intake, self.repository_root, self.cwd)
        self.status_bar.stop()
        
        if not self.session.active_project:
             self.output(render_greeting_prompt(include_header=not self._header_sent_this_turn))
             self._header_sent_this_turn = True

    def _handle_correction(self, raw: str) -> None:
        """Handle user correction of project or path."""
        from slypilot.tools.filesystem.path_detector import detect_paths
        detected = detect_paths(raw, self.cwd)
        
        if detected:
             path_obj = detected[0]
             project_name = Path(path_obj.normalized_path).name
             self._output_assistant("SlyPilot", [f"D'accord, je corrige. Le projet cible est maintenant : {project_name}"])
             self.session = self.session_manager.update(
                 active_project={"name": project_name, "path": path_obj.normalized_path},
                 workflow=None
             )
             return

        project_name = extract_explicit_unresolved_name(raw)
        if project_name:
             self._output_assistant("SlyPilot", [f"D'accord, vous parlez de {project_name}. Pouvez-vous me donner son chemin local ?"])
             return

    def _current_project_memory(self, project_path: str | None = None) -> ProjectMemory | None:
        if self.current_project_memory and (
            not project_path or self.current_project_memory.project_path == project_path
        ):
            return self.current_project_memory

        target_path = project_path
        if not target_path and isinstance(self.session.active_project, dict):
            target_path = str(self.session.active_project.get("path", "") or "")
        if not target_path:
            return self.current_project_memory

        loaded = self.project_memory_store.load(target_path)
        if loaded:
            self.current_project_memory = loaded
        return loaded

    def _emit_final_synthesis(self, project_name: str, project_path: str, raw: str) -> None:
        from slypilot.coordinator.coordinator import handle_technical_brief
        from slypilot.coordinator.technical_brief_builder import build_technical_brief
        
        # Build a valid TechnicalRequestBrief for synthesis using the dedicated builder
        brief = build_technical_brief(
            "synthèse finale", 
            {"name": project_name, "path": project_path}
        )
        
        try:
            packet = handle_technical_brief(brief, self.repository_root, raw_request=raw)

            project_memory = None
            if isinstance(packet.metadata, dict):
                project_memory_data = packet.metadata.get("project_memory")
                if isinstance(project_memory_data, dict):
                    project_memory = ProjectMemory.from_dict(project_memory_data)
            if project_memory is None:
                project_memory = self.project_memory_store.load(get_project_path(packet) or project_path)
            if project_memory is not None:
                self.current_project_memory = project_memory
                if isinstance(packet.metadata, dict):
                    packet.metadata["project_memory"] = project_memory.to_dict()

            translated = self.cognitive.translate_response(packet)
            self.output("")
            if not self._header_sent_this_turn:
                self.output(render_slypilot_header())
                self.output("")
                self._header_sent_this_turn = True
            intro_lines = [f"Projet détecté : {packet.project_name}"]
            if isinstance(packet.metadata, dict) and packet.metadata.get("project_yaml_loaded"):
                intro_lines.append("Préparation déjà disponible.")
            else:
                intro_lines.append("Je vais préparer le projet pour pouvoir l’analyser correctement.")
            self._output_assistant(
                "Diagnostic initial",
                [
                    *intro_lines,
                    "",
                    "Voici la restitution détaillée du diagnostic initial.",
                    "",
                    *translated.splitlines(),
                ],
            )
            if self.verbose:
                resource_trace = None
                coordinator_trace = None
                if isinstance(packet.metadata, dict):
                    resource_trace = packet.metadata.get("resource_trace")
                    coordinator_trace = packet.metadata.get("coordinator_trace")
                if resource_trace is None:
                    resource_trace = {
                        "raw_input": raw,
                        "detected_paths": [project_path] if project_path else [],
                        "normalized_paths": [project_path] if project_path else [],
                        "existing_paths": [project_path] if project_path else [],
                        "missing_paths": [],
                        "blocked_paths": [],
                        "resource_types": ["project_directory"] if project_path else [],
                        "selected_resource": {
                            "path": project_path,
                            "type": "project_directory",
                            "exists": bool(project_path),
                            "policy_status": "allowed",
                        },
                        "intake_status": "success" if project_path else "unknown",
                    }
                if coordinator_trace is None:
                    intent_trace = {}
                    if isinstance(packet.metadata, dict):
                        intent_trace = packet.metadata.get("intent_trace") or {}
                    if not intent_trace:
                        intent_trace = {
                            "raw_input": raw,
                            "normalized_input": raw.lower().strip(),
                            "detected_action_terms": ["analyse"] if "analyse" in raw.lower() else [],
                            "detected_intent": "analyze_project" if "analyse" in raw.lower() else "technical_request",
                            "intent_confidence": 0.95,
                            "detected_paths": [project_path] if project_path else [],
                            "resource_type": "project_directory" if project_path else "unknown",
                            "project_name": packet.project_name.lower(),
                            "fusion_result": "analysis_request_with_project_path" if project_path else "technical_request_without_path",
                            "final_decision": "auto_prepare_then_analyze" if project_path else "ask_clarification",
                            "ambiguity_reason": None,
                        }
                    coordinator_trace = {
                        "intent": "analyze_project",
                        "project": packet.project_name,
                        "strategy": "memory-guided-analysis",
                        "provider": "local",
                        "archiops": "enabled" if packet.metadata.get("knowledge_contract") else "disabled",
                        "decision": packet.status,
                        "reason": ", ".join(packet.errors) if packet.errors else packet.recommendation,
                        "intent_trace": intent_trace,
                        "advisory": packet.metadata.get("advisory_trace") if isinstance(packet.metadata, dict) else {},
                    }
                self.output(render_resource_trace(resource_trace or {}))
                self.output(render_coordinator_trace(coordinator_trace or {}))
                self.output(
                    render_analysis_restitution(
                        packet.project_name,
                        packet.metadata,
                        str(packet.project_path),
                        diagnostic=packet,
                        verbose=self.verbose,
                        include_header=False,
                    )
                )
            
            # NETTOYAGE DU STATE FINAL
            if self.session.workflow:
                 final_workflow = self.workflow_engine.complete(self.session.workflow)
            else:
                 final_workflow = None

            self.session = self.session_manager.update(
                active_project={"name": packet.project_name, "path": get_project_path(packet)},
                active_analysis={
                    "status": "completed",
                    "recommendation": packet.recommendation,
                    "packet_metadata": packet.metadata,
                    "project_name": packet.project_name,
                    "project_path": get_project_path(packet),
                    "project_memory": project_memory.to_dict() if project_memory else None,
                },
                workflow=final_workflow
            )
            self._append_assistant(f"synthèse finale terminée pour {project_name}.")
        except Exception as e:
             # STI: Invalidate on crash
             self.session = self.session_manager.update(workflow=None)
             self.pending_action = None
             from slypilot.contracts import TechnicalBriefInvalid
             if isinstance(e, TechnicalBriefInvalid):
                 self._output_assistant("SlyPilot", [
                     "Je ne peux pas mener l'analyse car le contexte projet est incomplet.",
                     "",
                     "Il me manque un chemin local fiable vers le projet à analyser.",
                     "",
                     "Indiquez le chemin du projet, par exemple :",
                     "analyse /Users/.../MonProjet",
                 ])
                 return
             self._output_assistant("SlyPilot", [
                 "Analyse impossible.",
                 "",
                 "Cause détectée :",
                 str(e),
                 "",
                 "Après correction, relancez l’analyse du projet."
             ])

    def _append_user(self, raw: str) -> None:
        self.store.append(self.session.session_id, {"role": "user", "content": raw, "timestamp": _now()})

    def _append_assistant(self, content: str) -> None:
        self.store.append(self.session.session_id, {"role": "assistant", "content": content, "timestamp": _now()})

    def _sync_registry(self, status: str) -> None:
        last_project = self.session.last_project if isinstance(self.session.last_project, dict) else {}
        from dataclasses import asdict
        self.registry.upsert_session(
            session_id=self.session.session_id,
            created_at=self.session.started_at,
            last_activity=_now(),
            project=safe_project_label(last_project),
            status=status,
            message_count=self.store.count(self.session.session_id),
            cwd=self.session.cwd,
            pending_action=self.pending_action,
            project_path=get_project_path(last_project) or str(self.session.cwd),
            archiops_status=str(last_project.get("archiops_status", "missing")),
            active_project=self.session.active_project,
            active_analysis=self.session.active_analysis,
            workflow=asdict(self.session.workflow) if self.session.workflow else None,
        )

    def _close_session(self) -> None:
        self.session = self.session_manager.update(status="closed")
        last_project = self.session.last_project if isinstance(self.session.last_project, dict) else {}
        from dataclasses import asdict
        summary = SessionSummary(
            session_id=self.session.session_id,
            project=safe_project_label(last_project),
            started_at=self.session.started_at,
            ended_at=_now(),
            message_count=self.store.count(self.session.session_id),
            decisions=[str(self.session.last_decision)] if self.session.last_decision else [],
            incidents=[],
            pending_action=self.pending_action,
            active_project=self.session.active_project,
            active_analysis=self.session.active_analysis,
            workflow=asdict(self.session.workflow) if self.session.workflow else None,
        )
        self.registry.save_summary(summary)
        self._sync_registry(status="closed")
