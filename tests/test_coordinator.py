from __future__ import annotations

from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from slypilot.coordinator import coordinate_request
from slypilot.coordinator.coherence_checker import CoherenceResult
from slypilot.coordinator.execution_guard import ExecutionGuardResult
from slypilot.coordinator.strategy_selector import StrategySelection
from slypilot.intake import build_intake
from slypilot.project_resolver import ResolvedProject


class CoordinatorTests(TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.barberexpert_root = Path("/Users/hakimradi/Nextcloud/SlyProjet/BarberExpert")

    def test_explicit_barberexpert_routes_to_barberexpert(self) -> None:
        intake = build_intake("analyse BarberExpert et identifie les bugs visibles", self.root)
        result = coordinate_request(
            intake,
            self.root,
            current_working_directory=self.barberexpert_root,
            dry_run=True,
        )

        self.assertTrue(result.decision.allowed)
        self.assertEqual(result.project.name, "barberexpert")
        self.assertIsNotNone(result.packet)
        self.assertEqual(result.trace.project, "barberexpert")
        self.assertEqual(result.trace.decision, "approved")

    def test_ambiguous_request_is_blocked(self) -> None:
        intake = build_intake("analyse SlyScan et BarberExpert", self.root)
        result = coordinate_request(
            intake,
            self.root,
            current_working_directory=self.barberexpert_root,
            dry_run=True,
        )

        self.assertFalse(result.decision.allowed)
        self.assertIsNone(result.packet)
        self.assertEqual(result.trace.decision, "blocked")
        self.assertTrue(result.project.mismatch_detected)

    def test_trace_is_structured(self) -> None:
        intake = build_intake("corrige bug upload SlyScan", self.root)
        result = coordinate_request(intake, self.root, dry_run=True)

        trace = result.trace.to_dict()
        self.assertIn("intent", trace)
        self.assertIn("project", trace)
        self.assertIn("strategy", trace)
        self.assertIn("provider", trace)
        self.assertIn("archiops", trace)
        self.assertIn("decision", trace)
        self.assertIn("reason", trace)
        self.assertTrue(result.resource.to_dict()["raw_input"])

    def test_provider_is_not_called_when_coherence_fails(self) -> None:
        intake = build_intake("analyse BarberExpert et identifie les bugs visibles", self.root)
        mismatch_project = ResolvedProject(
            name="slyscan",
            provider="deepseek",
            environment="local",
            requested_project="barberexpert",
            resolution_source="explicit_request",
            confidence="high",
            fallback_used=False,
            mismatch_detected=True,
        )

        with patch("slypilot.coordinator.coordinator.resolve_project", return_value=mismatch_project), patch(
            "slypilot.coordinator.coordinator.build_task_packet"
        ) as mocked_build_packet:
            result = coordinate_request(
                intake,
                self.root,
                current_working_directory=self.barberexpert_root,
                dry_run=False,
                live_run=True,
            )

        self.assertFalse(result.decision.allowed)
        self.assertEqual(result.coherence, CoherenceResult(False, "project_mismatch_detected"))
        self.assertEqual(result.guard, ExecutionGuardResult(False, "project_mismatch_detected"))
        self.assertEqual(result.strategy, StrategySelection("provider_execution", "live_run_requested"))
        self.assertIsNone(result.packet)
        self.assertEqual(result.block_reason, "project_mismatch_detected")
        mocked_build_packet.assert_not_called()

    def test_explicit_path_resolves_project_from_resource(self) -> None:
        intake = build_intake(
            "analyse mon projet /Users/hakimradi/Nextcloud/SlyProjet/SlyAudit",
            self.root,
        )
        result = coordinate_request(
            intake,
            self.root,
            current_working_directory=self.barberexpert_root,
            dry_run=True,
        )

        self.assertEqual(result.project.name, "slyaudit")
        self.assertEqual(result.project.resolution_source, "explicit_path")
        self.assertIn("/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit", result.resource.detected_paths)
        self.assertIn(result.resource.intake_status, {"init_required", "success"})

    def test_missing_path_blocks_execution(self) -> None:
        intake = build_intake("analyse /Users/hakimradi/Nextcloud/SlyProjet/FakeProject", self.root)
        result = coordinate_request(
            intake,
            self.root,
            current_working_directory=self.barberexpert_root,
            dry_run=True,
        )

        self.assertFalse(result.decision.allowed)
        self.assertEqual(result.block_reason, "local path does not exist")
        self.assertEqual(result.resource.intake_status, "missing_path")

    def test_sensitive_path_blocks_execution(self) -> None:
        intake = build_intake("analyse ~/.ssh", self.root)
        result = coordinate_request(
            intake,
            self.root,
            current_working_directory=self.barberexpert_root,
            dry_run=True,
        )

        self.assertFalse(result.decision.allowed)
        self.assertEqual(result.block_reason, "sensitive path blocked")
        self.assertEqual(result.resource.intake_status, "blocked")

    def test_multiple_paths_require_clarification(self) -> None:
        intake = build_intake(
            "analyse /Users/hakimradi/Nextcloud/SlyProjet/SlyAudit et /Users/hakimradi/Nextcloud/SlyProjet/SlyPilot",
            self.root,
        )
        result = coordinate_request(
            intake,
            self.root,
            current_working_directory=self.barberexpert_root,
            dry_run=True,
        )

        self.assertFalse(result.decision.allowed)
        self.assertEqual(result.strategy.name, "ask_clarification")
        self.assertEqual(result.block_reason, "multiple local paths detected")


if __name__ == "__main__":
    import unittest

    unittest.main()
