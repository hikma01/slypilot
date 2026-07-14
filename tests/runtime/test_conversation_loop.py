"""Interactive conversation loop tests."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from slypilot.cognitive.cognitive_interface import CognitiveInterface
from slypilot.contracts import TechnicalResponsePacket
from slypilot.runtime.conversation_loop import ConversationLoop


class _FakeResource:
    def __init__(self, intake_status: str = "success", path: str = "", resource_type: str = "") -> None:
        self.intake_status = intake_status
        self.detected_paths = [path] if path else []
        self.selected_resource = {"path": path, "type": resource_type, "exists": bool(path), "policy_status": "allowed"}

    def to_dict(self) -> dict[str, object]:
        return {
            "raw_input": "raw",
            "detected_paths": self.detected_paths,
            "normalized_paths": self.detected_paths,
            "existing_paths": self.detected_paths,
            "missing_paths": [],
            "blocked_paths": [],
            "resource_types": [self.selected_resource["type"]] if self.selected_resource["type"] else [],
            "selected_resource": self.selected_resource,
            "intake_status": self.intake_status,
        }


def _fake_result(
    task_type: str,
    project: str,
    *,
    intake_status: str = "success",
    decision_allowed: bool = True,
    decision_reason: str = "approved",
    path: str = "",
    resource_type: str = "",
    intent_trace: dict[str, object] | None = None,
    advisory_trace: dict[str, object] | None = None,
) -> SimpleNamespace:
    default_intent_trace = {}
    if path and resource_type in {"project_directory", "git_repository", "archiops_project"} and task_type != "unknown":
        default_intent_trace = {
            "raw_input": f"analyse {path}",
            "normalized_input": f"analyse {path.lower()}",
            "detected_action_terms": ["analyse"],
            "detected_intent": "analyze_project",
            "intent_confidence": 0.95,
            "detected_paths": [path],
            "resource_type": resource_type,
            "project_name": project,
            "fusion_result": "analysis_request_with_project_path",
            "final_decision": "auto_prepare_then_analyze",
            "ambiguity_reason": None,
        }
    return SimpleNamespace(
        intent=SimpleNamespace(classification=SimpleNamespace(task_type=task_type)),
        project=SimpleNamespace(name=project, requested_project=project, resolution_source="explicit_request", status="success", fallback_used=False),
        resource=_FakeResource(intake_status=intake_status, path=path, resource_type=resource_type),
        decision=SimpleNamespace(allowed=decision_allowed, reason=decision_reason),
        trace=SimpleNamespace(
            to_dict=lambda: {
                "project": project,
                "decision": decision_reason,
                "intent_trace": intent_trace or default_intent_trace,
                "advisory": advisory_trace or {},
            }
        ),
        packet=SimpleNamespace(project_path=path, metadata={"selected_maps": [], "knowledge_contract": {}}, warnings=[]),
        diagnostic=SimpleNamespace(recommendation="Explorer métier", next_step=["explorer"], confidence="bonne"),
        block_reason=None,
    )


class ConversationLoopTests(TestCase):
    def test_loop_waits_until_exit(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            inputs = iter(["exit"])
            outputs: list[str] = []

            def fake_input(_: str) -> str:
                return next(inputs)

            loop = ConversationLoop(root, root, input_func=fake_input, output_func=outputs.append)
            code = loop.run()

        self.assertEqual(code, 0)
        joined = "\n".join(outputs)
        self.assertIn("Assistant de coordination technique.", joined)
        self.assertIn("Session fermée.", joined)

    def test_pending_action_is_kept_until_confirmation(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            # 6 steps plan
            inputs = iter(["analyse /Users/hakimradi/Nextcloud/SlyProjet/SlyAudit", "ok", "ok", "ok", "ok", "ok", "ok", "ok", "exit"])
            outputs: list[str] = []

            def fake_input(_: str) -> str:
                return next(inputs)

            with patch(
                "slypilot.runtime.conversation_loop.coordinate_request",
                return_value=_fake_result(
                    "analyze_project",
                    "SlyAudit",
                    intake_status="init_required",
                    path="/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit",
                    resource_type="project_directory",
                ),
            ):
                loop = ConversationLoop(root, root, input_func=fake_input, output_func=outputs.append)
                self.assertEqual(loop.run(), 0)

        joined = "\n".join(outputs)
        self.assertIn("Projet détecté : SlyAudit", joined)
        self.assertIn("Je vais préparer le projet pour pouvoir l’analyser correctement.", joined)
        self.assertIn("Voici la restitution détaillée du diagnostic initial.", joined)

    def test_clarification_choice_is_resolved(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            project_root = root / "demo"
            project_root.mkdir()
            # Choice 1 then follow the sequential steps (6 steps)
            inputs = iter([f"analyse {project_root}", "1", "ok", "ok", "ok", "ok", "ok", "ok", "ok", "exit"])
            outputs: list[str] = []

            def fake_input(_: str) -> str:
                return next(inputs)

            initial_result = _fake_result(
                "debug", # Not unknown, otherwise it shows greeting
                "demo",
                path=str(project_root),
                resource_type="project_directory",
                decision_allowed=False,
                decision_reason="ambiguous_request",
            )
            # Disable expert flow so it falls back to the ambiguity prompt
            initial_result.trace.to_dict = lambda: {"intent_trace": {}}
            
            followup_result = _fake_result("analyze_project", "demo", path=str(project_root), resource_type="project_directory")

            with patch("slypilot.runtime.conversation_loop.coordinate_request", side_effect=[initial_result, followup_result, followup_result]):
                loop = ConversationLoop(root, project_root, input_func=fake_input, output_func=outputs.append)
                self.assertEqual(loop.run(), 0)

        joined = "\n".join(outputs)
        self.assertIn("Projet détecté : demo", joined)
        self.assertIn("Je comprends votre demande sur demo.", joined)
        self.assertIn("Action sélectionnée :", joined)
        self.assertIn("Voici la restitution détaillée du diagnostic initial.", joined)

    def test_analysis_request_auto_prepares_project(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            project_root = root / "SlyAudit"
            project_root.mkdir()
            # Follow sequential steps
            inputs = iter([f"analyse mon projet {project_root}", "ok", "ok", "ok", "ok", "ok", "ok", "ok", "ok", "exit"])

            outputs: list[str] = []

            def fake_input(_: str) -> str:
                return next(inputs)

            fake_result = _fake_result(
                "analyze_project",
                "SlyAudit",
                intake_status="init_required",
                path=str(project_root),
                resource_type="project_directory",
            )

            with patch("slypilot.runtime.conversation_loop.coordinate_request", return_value=fake_result):
                loop = ConversationLoop(root, project_root, input_func=fake_input, output_func=outputs.append)
                self.assertEqual(loop.run(), 0)

        joined = "\n".join(outputs)
        self.assertIn("Je vais préparer le projet pour pouvoir l’analyser correctement.", joined)
        self.assertIn("Voici la restitution détaillée du diagnostic initial.", joined)

    def test_analysis_without_path_requests_local_path(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            outputs: list[str] = []
            inputs = iter(["analyse", "exit"])

            def fake_input(_: str) -> str:
                return next(inputs)

            loop = ConversationLoop(root, root, input_func=fake_input, output_func=outputs.append)
            self.assertEqual(loop.run(), 0)

        joined = "\n".join(outputs)
        self.assertIn("chemin local du projet", joined)
        self.assertIn("analyse /Users/.../MonProjet", joined)
        self.assertNotIn("Je lance l’analyse technique en profondeur", joined)

    def test_analysis_then_project_path_restarts_flow(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            project_root = root / "SlyAudit"
            project_root.mkdir()
            outputs: list[str] = []
            inputs = iter(["analyse", f"voici mon projet {project_root}", "exit"])

            def fake_input(_: str) -> str:
                return next(inputs)

            with patch.object(ConversationLoop, "_start_technical_analysis") as mocked_start:
                loop = ConversationLoop(root, root, input_func=fake_input, output_func=outputs.append)
                self.assertEqual(loop.run(), 0)

            mocked_start.assert_called_once()
            project_name, project_path, raw = mocked_start.call_args.args[-3:]
            self.assertEqual(project_name, "SlyAudit")
            self.assertTrue(project_path.endswith("/SlyAudit"))
            self.assertIn("voici mon projet", raw)

        joined = "\n".join(outputs)
        self.assertIn("chemin local du projet", joined)

    def test_analysis_request_with_ready_project_runs_expert_flow(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            project_root = root / "SlyAudit"
            project_root.mkdir()
            (project_root / "Documents" / "ARCHIOPS").mkdir(parents=True)
            (project_root / "Documents" / "ARCHIOPS" / "project.yaml").touch()

            # Follow sequential steps
            inputs = iter([f"analyse mon projet {project_root}", "ok", "ok", "ok", "ok", "ok", "ok", "ok", "ok", "exit"])

            outputs: list[str] = []

            def fake_input(_: str) -> str:
                return next(inputs)

            fake_result = _fake_result(
                "analyze_project",
                "SlyAudit",
                intake_status="success",
                path=str(project_root),
                resource_type="project_directory",
            )

            with patch("slypilot.runtime.conversation_loop.coordinate_request", return_value=fake_result):
                loop = ConversationLoop(root, project_root, input_func=fake_input, output_func=outputs.append)
                self.assertEqual(loop.run(), 0)

        joined = "\n".join(outputs)
        self.assertIn("Je vais préparer le projet pour pouvoir l’analyser correctement.", joined)
        self.assertIn("Voici la restitution détaillée du diagnostic initial.", joined)

    def test_final_synthesis_uses_project_memory_and_translator(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            project_root = root / "SlyAudit"
            project_root.mkdir()
            outputs: list[str] = []

            packet = TechnicalResponsePacket(
                project_name="SlyAudit",
                project_path=str(project_root),
                status="success",
                stack_detected=True,
                technologies=["Python", "Docker"],
                architecture_summary="Structure globale cartographiée.",
                business_summary="Cœur métier en cours d'identification.",
                risks=["cartographie encore initiale"],
                generated_files=["slypilot/packets/generated/task_123.md"],
                raw_references=[{"path": "Documents/ARCHIOPS/repo-map.md"}],
                metadata={
                    "selected_maps": ["Documents/ARCHIOPS/repo-map.md", "Documents/ARCHIOPS/runtime-map.md"],
                    "selected_files": ["docker-compose.yml", "requirements.txt"],
                    "project_memory": {
                        "project_name": "SlyAudit",
                        "project_path": str(project_root),
                        "technologies": ["Python", "Docker"],
                        "domains": ["api", "config"],
                        "architecture_summary": "La structure semble conteneurisée autour de Python.",
                        "business_summary": "Le cœur métier n'est pas encore entièrement isolé.",
                        "runtime_summary": "Python + Docker.",
                        "risks": ["cartographie encore initiale"],
                        "important_files": ["docker-compose.yml", "requirements.txt"],
                        "entry_points": ["/api/v1/"],
                        "loaded_maps": {
                            "repo_map": "# REPO MAP",
                            "runtime_map": "# RUNTIME MAP",
                        },
                        "generated_artifacts": ["slypilot/packets/generated/task_123.md"],
                        "previous_findings": ["La cartographie reste à enrichir."],
                        "active_recommendation": "Explorer l'arborescence métier.",
                        "last_analysis_timestamp": "2026-06-05T00:00:00+00:00",
                    },
                },
                errors=[],
                recommendation="Explorer l'arborescence métier.",
            )

            def fake_handle_technical_brief(*args: object, **kwargs: object) -> TechnicalResponsePacket:
                return packet

            with patch("slypilot.coordinator.coordinator.handle_technical_brief", side_effect=fake_handle_technical_brief):
                loop = ConversationLoop(root, project_root, output_func=outputs.append)
                with patch.object(CognitiveInterface, "translate_response", wraps=loop.cognitive.translate_response) as mocked_translate:
                    loop._emit_final_synthesis("SlyAudit", str(project_root), "analyse /Users/hakimradi/Nextcloud/SlyProjet/SlyAudit")
                    self.assertTrue(mocked_translate.called)

        joined = "\n".join(outputs)
        self.assertIn("Voici la restitution détaillée du diagnostic initial.", joined)
        self.assertIn("Mémoire projet", joined)
        self.assertIn("Technologies mémorisées", joined)
        self.assertIn("Python (langage principal du projet)", joined)

    def test_analysis_failure_shows_explicit_reason(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            project_root = root / "SlyAudit"
            project_root.mkdir()
            inputs = iter([f"analyse {project_root}", "1", "ok", "ok", "ok", "ok", "ok", "ok", "exit"])
            outputs: list[str] = []

            def fake_input(_: str) -> str:
                return next(inputs)

            failure_result = type(
                "Fail",
                (),
                {
                    "intent": type("I", (), {"classification": type("C", (), {"task_type": "analyze_project"})()})(),
                    "decision": type("D", (), {"allowed": False, "reason": "access_denied"})(),
                    "project": type("P", (), {"name": "SlyAudit", "requested_project": "SlyAudit", "resolution_source": "explicit", "status": "success", "fallback_used": False})(),
                    "resource": type("R", (), {"intake_status": "success", "selected_resource": {"path": str(project_root), "type": "project_directory"}, "to_dict": lambda self=None: {}})(),
                    "block_reason": "denied",
                    "packet": None,
                    "trace": type("T", (), {"to_dict": lambda *args: {"intent_trace": {"final_decision": "auto_prepare_then_analyze"}}})()
                },
            )()


            with patch("slypilot.coordinator.coordinator.handle_technical_brief", side_effect=Exception("denied")):
                loop = ConversationLoop(root, project_root, input_func=fake_input, output_func=outputs.append)
                self.assertEqual(loop.run(), 0)

        joined = "\n".join(outputs)
        self.assertIn("Analyse impossible.", joined)
        self.assertIn("denied", joined)

    def test_interactive_debug_emits_traces_for_analysis_request(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            project_root = root / "SlyCRM"
            project_root.mkdir()
            # Follow sequential steps
            inputs = iter([f"analyse mon projet {project_root}", "ok", "ok", "ok", "ok", "ok", "ok", "ok", "ok", "exit"])

            outputs: list[str] = []

            def fake_input(_: str) -> str:
                return next(inputs)

            intent_trace = {
                "raw_input": f"analyse mon projet {project_root}",
                "normalized_input": f"analyse mon projet {str(project_root).lower()}",
                "detected_action_terms": ["analyse"],
                "detected_intent": "analyze_project",
                "intent_confidence": 0.95,
                "detected_paths": [str(project_root)],
                "resource_type": "project_directory",
                "project_name": "slycrm",
                "fusion_result": "analysis_request_with_project_path",
                "final_decision": "auto_prepare_then_analyze",
                "ambiguity_reason": None,
            }
            fake_result = _fake_result(
                "analyze_project",
                "slycrm",
                path=str(project_root),
                resource_type="project_directory",
                intent_trace=intent_trace,
            )

            with patch("slypilot.runtime.conversation_loop.coordinate_request", return_value=fake_result):
                loop = ConversationLoop(root, project_root, input_func=fake_input, output_func=outputs.append, verbose=True)
                self.assertEqual(loop.run(), 0)

        joined = "\n".join(outputs)
        self.assertIn("RESOURCE TRACE", joined)
        self.assertIn("COORDINATOR TRACE", joined)
        self.assertIn("INTENT_TRACE", joined)
        self.assertIn("detected_intent", joined)
        self.assertIn("fusion_result", joined)
        self.assertIn("final_decision", joined)
        self.assertIn("Voici la restitution détaillée du diagnostic initial.", joined)

    def test_draft_preview_remains_for_non_analysis_request(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            project_root = root / "SlyAudit"
            project_root.mkdir()
            outputs: list[str] = []

            with patch(
                "slypilot.runtime.conversation_loop.coordinate_request",
                return_value=_fake_result(
                    "architecture",
                    "SlyAudit",
                    path=str(project_root),
                    resource_type="project_directory",
                ),
            ):
                loop = ConversationLoop(root, root, output_func=outputs.append)
                loop._handle_message("architecture review")

        joined = "\n".join(outputs)
        self.assertIn("Bonjour. Je peux t'aider à analyser un projet", joined)
        self.assertNotIn("Que veux-tu faire ?", joined)

    def test_post_diagnostic_ok_cycle_finishes_without_restarting(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            project_root = root / "SlyAudit"
            project_root.mkdir()
            inputs = iter([
                f"analyse {project_root}",
                "ok",
                "ok",
                "ok",
                "ok",
                "ok",
                "exit",
            ])
            outputs: list[str] = []

            def fake_input(_: str) -> str:
                return next(inputs)

            fake_result = _fake_result(
                "analyze_project",
                "SlyAudit",
                intake_status="success",
                path=str(project_root),
                resource_type="project_directory",
            )

            with patch("slypilot.runtime.conversation_loop.coordinate_request", return_value=fake_result):
                loop = ConversationLoop(root, project_root, input_func=fake_input, output_func=outputs.append)
                self.assertEqual(loop.run(), 0)

        joined = "\n".join(outputs)
        self.assertIn("Prochaine étape recommandée", joined)
        self.assertIn("Analyser les fichiers importants", joined)
        self.assertIn("Structure détectée", joined)
        self.assertIn("Zones à risque visibles", joined)
        self.assertIn("Analyse arrêtée. Le contexte projet reste disponible.", joined)
        self.assertNotIn("Souhaitez-vous", joined)
        self.assertNotIn("On ne pose pas de pansement", joined)
