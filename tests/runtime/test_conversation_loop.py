from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

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
        project=SimpleNamespace(name=project, requested_project=project, resolution_source="explicit_request"),
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
        packet=SimpleNamespace(packet_path=Path("/tmp/packet.md"), metadata={"selected_maps": []}, warnings=[]),
    )


class ConversationLoopTests(TestCase):
    def test_loop_waits_until_exit(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            inputs = iter(["analyse architecture SlyPilot", "exit"])
            outputs: list[str] = []

            def fake_input(_: str) -> str:
                return next(inputs)

            with patch(
                "slypilot.runtime.conversation_loop.coordinate_request",
                return_value=_fake_result("architecture", "slypilot"),
            ):
                loop = ConversationLoop(root, root, input_func=fake_input, output_func=outputs.append)
                code = loop.run()

        self.assertEqual(code, 0)
        joined = "\n".join(outputs)
        self.assertIn("Session :", joined)
        self.assertIn("Mode brouillon", joined)
        self.assertIn("Session fermée.", joined)

    def test_exit_and_quit_commands_close_session(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            for command in ("exit", "quit"):
                inputs = iter([command])
                outputs: list[str] = []

                def fake_input(_: str) -> str:
                    return next(inputs)

                loop = ConversationLoop(root, root, input_func=fake_input, output_func=outputs.append)
                self.assertEqual(loop.run(), 0)
                self.assertIn("Session fermée.", "\n".join(outputs))

    def test_pending_action_is_kept_until_confirmation(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            inputs = iter(["analyse /Users/hakimradi/Nextcloud/SlyProjet/SlyAudit", "exit"])
            outputs: list[str] = []

            def fake_input(_: str) -> str:
                return next(inputs)

            with patch(
                "slypilot.runtime.conversation_loop.coordinate_request",
                return_value=_fake_result(
                    "debug",
                    "slyaudit",
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
        self.assertIn("Préparation du projet : en cours", joined)
        self.assertIn("Préparation du projet : terminé", joined)
        self.assertIn("Analyse : terminé", joined)
        self.assertIn("Préparation du diagnostic initial...", joined)
        self.assertIn("Diagnostic initial :", joined)
        self.assertNotIn("ARCHI OPS est la cartographie technique utilisée par SlyPilot.", joined)
        self.assertNotIn("Souhaites-tu initialiser", joined)

    def test_clarification_choice_is_resolved(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            inputs = iter(["/tmp/demo /tmp/other", "1", "exit"])
            outputs: list[str] = []

            def fake_input(_: str) -> str:
                return next(inputs)

            with patch(
                "slypilot.runtime.conversation_loop.coordinate_request",
                side_effect=[
                    _fake_result(
                        "debug",
                        "unknown",
                        decision_allowed=False,
                        decision_reason="multiple local paths detected",
                        path="/tmp/demo",
                        resource_type="project_directory",
                    ),
                    _fake_result(
                        "architecture",
                        "slyaudit",
                        path="/tmp/demo",
                        resource_type="project_directory",
                    ),
                ],
            ):
                loop = ConversationLoop(root, root, input_func=fake_input, output_func=outputs.append)
                self.assertEqual(loop.run(), 0)

        joined = "\n".join(outputs)
        self.assertIn("J'ai détecté une ressource locale", joined)
        self.assertIn("Action sélectionnée :", joined)
        self.assertIn("Analyser le projet", joined)
        self.assertIn("Diagnostic initial :", joined)

    def test_analysis_request_auto_prepares_project(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            project_root = root / "SlyAudit"
            project_root.mkdir()
            inputs = iter([f"analyse {project_root}", "exit"])
            outputs: list[str] = []

            def fake_input(_: str) -> str:
                return next(inputs)

            with patch(
                "slypilot.runtime.conversation_loop.coordinate_request",
                side_effect=[
                    _fake_result(
                        "debug",
                        "slyaudit",
                        intake_status="init_required",
                        path=str(project_root),
                        resource_type="project_directory",
                    ),
                    _fake_result(
                        "architecture",
                        "slyaudit",
                        intake_status="success",
                        path=str(project_root),
                        resource_type="project_directory",
                    ),
                ],
            ):
                loop = ConversationLoop(root, project_root, input_func=fake_input, output_func=outputs.append)
                self.assertEqual(loop.run(), 0)

        joined = "\n".join(outputs)
        self.assertIn("Je vais préparer le projet pour pouvoir l’analyser correctement.", joined)
        self.assertIn("Préparation du projet : en cours", joined)
        self.assertIn("Préparation du diagnostic initial...", joined)
        self.assertIn("Diagnostic initial :", joined)

    def test_analysis_request_with_ready_project_runs_expert_flow(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            project_root = root / "SlyAudit"
            project_root.mkdir()
            inputs = iter([f"analyse mon projet {project_root}", "exit"])
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
                "project_name": "slyaudit",
                "fusion_result": "analysis_request_with_project_path",
                "final_decision": "auto_prepare_then_analyze",
                "ambiguity_reason": None,
            }

            with patch(
                "slypilot.runtime.conversation_loop.coordinate_request",
                side_effect=[
                    _fake_result(
                        "analyze_project",
                        "slyaudit",
                        intake_status="success",
                        path=str(project_root),
                        resource_type="project_directory",
                        intent_trace=intent_trace,
                        advisory_trace={
                            "advisory": "recommendation",
                            "diagnosis": "Projet détecté, ARCHI OPS disponible",
                            "capability_level": "Niveau 1",
                            "recommended_action": "analyser slyaudit avec ARCHI OPS",
                            "alternatives": ["analyse minimale", "afficher l’état du projet"],
                            "recommendation_reason": "ARCHI OPS fournit déjà la cartographie et les conventions nécessaires pour une analyse bornée.",
                            "confidence": "high",
                        },
                    ),
                    _fake_result(
                        "analyze_project",
                        "slyaudit",
                        intake_status="success",
                        path=str(project_root),
                        resource_type="project_directory",
                        intent_trace=intent_trace,
                        advisory_trace={
                            "advisory": "recommendation",
                            "diagnosis": "Projet détecté, ARCHI OPS disponible",
                            "capability_level": "Niveau 1",
                            "recommended_action": "analyser slyaudit avec ARCHI OPS",
                            "alternatives": ["analyse minimale", "afficher l’état du projet"],
                            "recommendation_reason": "ARCHI OPS fournit déjà la cartographie et les conventions nécessaires pour une analyse bornée.",
                            "confidence": "high",
                        },
                    ),
                ],
            ):
                loop = ConversationLoop(root, project_root, input_func=fake_input, output_func=outputs.append)
                self.assertEqual(loop.run(), 0)

        joined = "\n".join(outputs)
        self.assertIn("Préparation déjà disponible.", joined)
        self.assertIn("Préparation du diagnostic initial...", joined)
        self.assertIn("Diagnostic initial :", joined)
        self.assertNotIn("Mode brouillon", joined)

    def test_analysis_failure_shows_explicit_reason(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            project_root = root / "SlyAudit"
            project_root.mkdir()
            inputs = iter([f"analyse {project_root}", "exit"])
            outputs: list[str] = []

            def fake_input(_: str) -> str:
                return next(inputs)

            with patch(
                "slypilot.runtime.conversation_loop.coordinate_request",
                side_effect=[
                    _fake_result(
                        "debug",
                        "slyaudit",
                        intake_status="init_required",
                        path=str(project_root),
                        resource_type="project_directory",
                    ),
                    SimpleNamespace(
                        intent=SimpleNamespace(classification=SimpleNamespace(task_type="architecture")),
                        project=SimpleNamespace(name="slyaudit", requested_project="slyaudit", resolution_source="explicit_path"),
                        resource=_FakeResource(intake_status="success", path=str(project_root), resource_type="project_directory"),
                        decision=SimpleNamespace(allowed=False, reason="project_mismatch_detected"),
                        trace=SimpleNamespace(to_dict=lambda: {"project": "slyaudit", "decision": "project_mismatch_detected"}),
                        packet=None,
                        block_reason="project_mismatch_detected",
                    ),
                ],
            ):
                loop = ConversationLoop(root, project_root, input_func=fake_input, output_func=outputs.append)
                self.assertEqual(loop.run(), 0)

        joined = "\n".join(outputs)
        self.assertIn("Analyse impossible.", joined)
        self.assertIn("Raison :", joined)
        self.assertIn("project_mismatch_detected", joined)

    def test_interactive_debug_emits_traces_for_analysis_request(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            project_root = root / "SlyCRM"
            project_root.mkdir()
            inputs = iter([f"analyse mon projet {project_root}", "exit"])
            outputs: list[str] = []

            def fake_input(_: str) -> str:
                return next(inputs)

            with patch(
                "slypilot.runtime.conversation_loop.coordinate_request",
                side_effect=[
                    _fake_result(
                        "analyze_project",
                        "slycrm",
                        intake_status="init_required",
                        path=str(project_root),
                        resource_type="project_directory",
                        intent_trace={
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
                        },
                        advisory_trace={
                            "advisory": "recommendation",
                            "diagnosis": "Projet détecté, ARCHI OPS disponible",
                            "capability_level": "Niveau 1",
                            "recommended_action": "analyser slycrm avec ARCHI OPS",
                            "alternatives": ["analyse minimale", "afficher l’état du projet"],
                            "recommendation_reason": "ARCHI OPS fournit déjà la cartographie et les conventions nécessaires pour une analyse bornée.",
                            "confidence": "high",
                        },
                    ),
                    _fake_result(
                        "analyze_project",
                        "slycrm",
                        intake_status="success",
                        path=str(project_root),
                        resource_type="project_directory",
                        intent_trace={
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
                        },
                        advisory_trace={
                            "advisory": "recommendation",
                            "diagnosis": "Projet détecté, ARCHI OPS disponible",
                            "capability_level": "Niveau 1",
                            "recommended_action": "analyser slycrm avec ARCHI OPS",
                            "alternatives": ["analyse minimale", "afficher l’état du projet"],
                            "recommendation_reason": "ARCHI OPS fournit déjà la cartographie et les conventions nécessaires pour une analyse bornée.",
                            "confidence": "high",
                        },
                    ),
                ],
            ), patch(
                "slypilot.runtime.conversation_loop.prepare_project",
                return_value=SimpleNamespace(preparation_status="success", errors=[], created_files=[]),
            ):
                loop = ConversationLoop(root, project_root, input_func=fake_input, output_func=outputs.append, verbose=True)
                self.assertEqual(loop.run(), 0)

        joined = "\n".join(outputs)
        self.assertIn("Projet détecté : SlyCRM", joined)
        self.assertIn("Préparation du diagnostic initial...", joined)
        self.assertIn("Diagnostic initial :", joined)
        self.assertIn("INTENT_TRACE", joined)
        self.assertIn("RESOURCE TRACE", joined)
        self.assertIn("ADVISORY_TRACE", joined)
        self.assertIn("COORDINATOR TRACE", joined)
        self.assertNotIn("Demande ambiguë.", joined)

    def test_draft_preview_remains_for_non_analysis_request(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            outputs: list[str] = []

            def fake_input(_: str) -> str:
                return "exit"

            with patch(
                "slypilot.runtime.conversation_loop.coordinate_request",
                return_value=_fake_result(
                    "architecture",
                    "slypilot",
                    intake_status="success",
                    path="",
                    resource_type="",
                    intent_trace={
                        "raw_input": "architecture review",
                        "normalized_input": "architecture review",
                        "detected_action_terms": [],
                        "detected_intent": "unknown",
                        "intent_confidence": 0.2,
                        "detected_paths": [],
                        "resource_type": "",
                        "project_name": "unknown",
                        "fusion_result": "no_resource",
                        "final_decision": "no_resource",
                        "ambiguity_reason": None,
                    },
                    advisory_trace={
                        "advisory": "recommendation",
                        "diagnosis": "Contexte insuffisant pour une recommandation forte",
                        "capability_level": "Niveau 0",
                        "recommended_action": "demander une clarification",
                        "alternatives": ["annuler"],
                        "recommendation_reason": "Le coordinateur ne dispose pas d'un contexte assez fiable pour recommander une action plus ambitieuse.",
                        "confidence": "medium",
                    },
                ),
            ):
                loop = ConversationLoop(root, root, input_func=fake_input, output_func=outputs.append)
                loop._handle_message("architecture review")

        joined = "\n".join(outputs)
        self.assertIn("Mode brouillon", joined)
        self.assertNotIn("Préparation du diagnostic initial...", joined)
