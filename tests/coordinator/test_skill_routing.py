from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from slypilot.intake import build_intake
from slypilot.coordinator.coordinator import coordinate_request


def _resource_result(raw_request: str, project_name: str, resource_type: str = "project_directory") -> SimpleNamespace:
    return SimpleNamespace(
        raw_input=raw_request,
        detected_paths=["/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit"],
        normalized_paths=["/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit"],
        existing_paths=["/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit"],
        missing_paths=[],
        blocked_paths=[],
        resource_types=[resource_type],
        selected_resource={
            "path": "/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit",
            "type": resource_type,
            "exists": True,
            "policy_status": "allowed",
        },
        intake_status="success",
        project_name=project_name,
        project_root="/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit",
        resource_trace={"selected_resource": {"path": "/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit", "type": resource_type}},
    )


def _intent_fusion(final_decision: str, detected_intent: str = "analyze_project", fusion_result: str = "analysis_request_with_project_path", resource_type: str = "project_directory") -> SimpleNamespace:
    return SimpleNamespace(
        raw_input="analyse",
        normalized_input="analyse",
        detected_action_terms=["analyse"],
        detected_intent=detected_intent,
        intent_confidence=0.95,
        detected_paths=["/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit"],
        resource_type=resource_type,
        project_name="slyaudit",
        fusion_result=fusion_result,
        final_decision=final_decision,
        ambiguity_reason=None,
        to_dict=lambda: {
            "raw_input": "analyse",
            "normalized_input": "analyse",
            "detected_action_terms": ["analyse"],
            "detected_intent": detected_intent,
            "intent_confidence": 0.95,
            "detected_paths": ["/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit"],
            "resource_type": resource_type,
            "project_name": "slyaudit",
            "fusion_result": fusion_result,
            "final_decision": final_decision,
            "ambiguity_reason": None,
        },
    )


class SkillRoutingTests(TestCase):
    def test_analysis_request_uses_project_analysis_skill(self) -> None:
        repository_root = Path("/Users/hakimradi/Nextcloud/SlyProjet/SlyPilot")
        intake = build_intake("analyse mon projet /Users/hakimradi/Nextcloud/SlyProjet/SlyAudit", repository_root)

        with patch("slypilot.coordinator.coordinator.load_coordinator_prompt", return_value=""), patch(
            "slypilot.coordinator.coordinator.resolve_resources",
            return_value=_resource_result(intake.raw_request, "slyaudit"),
        ), patch(
            "slypilot.coordinator.coordinator.resolve_intent_with_resource",
            return_value=_intent_fusion("auto_prepare_then_analyze"),
        ), patch(
            "slypilot.coordinator.coordinator.analyze_intent",
            return_value=SimpleNamespace(task_type="analyze_project", confidence="high", classification=SimpleNamespace(task_type="architecture")),
        ), patch(
            "slypilot.coordinator.coordinator.resolve_project",
            return_value=SimpleNamespace(name="slyaudit", provider="deepseek", environment="local", requested_project="slyaudit"),
        ), patch(
            "slypilot.coordinator.coordinator.check_coherence",
            return_value=SimpleNamespace(allowed=True, reason="ok"),
        ), patch(
            "slypilot.coordinator.coordinator.guard_execution",
            return_value=SimpleNamespace(allowed=True, reason="allowed"),
        ), patch(
            "slypilot.coordinator.coordinator.decide",
            return_value=SimpleNamespace(allowed=True, reason="approved", strategy=SimpleNamespace(name="packet_preview")),
        ), patch(
            "slypilot.coordinator.coordinator.build_task_packet",
            return_value=SimpleNamespace(metadata={"selected_maps": []}, packet_path=Path("/tmp/packet.md"), warnings=[]),
        ):
            result = coordinate_request(intake, repository_root, current_working_directory=repository_root)

        self.assertEqual(result.trace.skill, "project_analysis_skill")

    def test_cartography_request_uses_cartography_skill(self) -> None:
        repository_root = Path("/Users/hakimradi/Nextcloud/SlyProjet/SlyPilot")
        intake = build_intake("affiche la cartographie de SlyAudit", repository_root)

        with patch("slypilot.coordinator.coordinator.load_coordinator_prompt", return_value=""), patch(
            "slypilot.coordinator.coordinator.resolve_resources",
            return_value=_resource_result(intake.raw_request, "slyaudit"),
        ), patch(
            "slypilot.coordinator.coordinator.resolve_intent_with_resource",
            return_value=_intent_fusion("ask_project_action_choice", detected_intent="unknown", fusion_result="project_path_needs_choice"),
        ), patch(
            "slypilot.coordinator.coordinator.analyze_intent",
            return_value=SimpleNamespace(task_type="architecture", confidence="high", classification=SimpleNamespace(task_type="architecture")),
        ), patch(
            "slypilot.coordinator.coordinator.resolve_project",
            return_value=SimpleNamespace(name="slyaudit", provider="deepseek", environment="local", requested_project="slyaudit"),
        ), patch(
            "slypilot.coordinator.coordinator.check_coherence",
            return_value=SimpleNamespace(allowed=True, reason="ok"),
        ), patch(
            "slypilot.coordinator.coordinator.guard_execution",
            return_value=SimpleNamespace(allowed=True, reason="allowed"),
        ), patch(
            "slypilot.coordinator.coordinator.decide",
            return_value=SimpleNamespace(allowed=True, reason="approved", strategy=SimpleNamespace(name="packet_preview")),
        ), patch(
            "slypilot.coordinator.coordinator.build_task_packet",
            return_value=SimpleNamespace(metadata={"selected_maps": []}, packet_path=Path("/tmp/packet.md"), warnings=[]),
        ):
            result = coordinate_request(intake, repository_root, current_working_directory=repository_root)

        self.assertEqual(result.trace.skill, "cartography_skill")
