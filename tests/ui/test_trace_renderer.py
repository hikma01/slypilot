from __future__ import annotations

from unittest import TestCase

from slypilot.coordinator.coordinator_trace import AdvisoryTrace, CoordinatorTrace, ResourceTrace
from slypilot.ui import render_coordinator_trace, render_resource_trace


class TraceRendererTests(TestCase):
    def test_resource_trace_is_rendered_separately(self) -> None:
        trace = ResourceTrace(
            raw_input="analyse",
            detected_paths=["/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit"],
            normalized_paths=["/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit"],
            existing_paths=["/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit"],
            missing_paths=[],
            blocked_paths=[],
            resource_types=["project_directory"],
            selected_resource={"path": "/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit", "type": "project_directory"},
            intake_status="init_required",
        )
        output = render_resource_trace(trace)
        self.assertIn("RESOURCE TRACE", output)
        self.assertIn("project_directory", output)
        self.assertIn("init_required", output)

    def test_coordinator_trace_is_rendered_separately(self) -> None:
        trace = CoordinatorTrace(
            intent={"type": "debug"},
            project={"requested_project": "slyaudit", "resolved_project": "slyaudit"},
            strategy={"selected_skill": "bug_analysis"},
            provider={"selected_provider": "deepseek"},
            archiops={"loaded": True},
            decision={"action": "proceed"},
            reason="ok",
            advisory=AdvisoryTrace(
                advisory="recommendation",
                diagnosis="Projet détecté, ARCHI OPS absent",
                capability_level="Niveau 0",
                recommended_action="initialiser ARCHI OPS",
                alternatives=["analyse minimale immédiate", "annuler"],
                recommendation_reason="test",
                confidence="high",
            ),
        )
        output = render_coordinator_trace(trace)
        self.assertIn("COORDINATOR TRACE", output)
        self.assertIn("ADVISORY_TRACE", output)
        self.assertIn("requested_project", output)
        self.assertIn("resolved_project", output)
        self.assertIn("skill", output)
        self.assertIn("proceed", output)
        self.assertIn("dry_run", output)
        self.assertIn("provider_called", output)


if __name__ == "__main__":
    import unittest

    unittest.main()
