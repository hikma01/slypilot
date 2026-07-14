from __future__ import annotations

from pathlib import Path
from unittest import TestCase

from slypilot.intake import build_intake
from slypilot.coordinator import coordinate_request


class IntentResourceFusionTests(TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[2]
        self.cwd = Path("/Users/hakimradi/Nextcloud/SlyProjet/SlyCRM")

    def test_analysis_with_local_path_is_not_ambiguous(self) -> None:
        intake = build_intake("analyse mon projet /Users/hakimradi/Nextcloud/SlyProjet/SlyCRM", self.root)
        result = coordinate_request(intake, self.root, current_working_directory=self.cwd, dry_run=True)

        self.assertEqual(result.intent.task_type, "analyze_project")
        self.assertEqual(result.resource.intake_status, "success")
        self.assertEqual(result.project.name, "slycrm")
        self.assertTrue(result.decision.allowed)
        self.assertFalse(result.project.mismatch_detected)
        self.assertEqual(result.trace.reason, "approved")
        self.assertIsNotNone(result.packet)

    def test_analysis_with_uppercase_request_is_not_ambiguous(self) -> None:
        intake = build_intake("Analyse mon projet /Users/hakimradi/Nextcloud/SlyProjet/SlyCRM", self.root)
        result = coordinate_request(intake, self.root, current_working_directory=self.cwd, dry_run=True)

        self.assertEqual(result.intent.task_type, "analyze_project")
        self.assertEqual(result.resource.intake_status, "success")
        self.assertEqual(result.project.name, "slycrm")
        self.assertTrue(result.decision.allowed)
        self.assertFalse(result.project.mismatch_detected)
        self.assertEqual(result.trace.reason, "approved")
        self.assertIsNotNone(result.packet)

    def test_path_only_still_requires_choice(self) -> None:
        intake = build_intake("/Users/hakimradi/Nextcloud/SlyProjet/SlyCRM", self.root)
        result = coordinate_request(intake, self.root, current_working_directory=self.cwd, dry_run=True)

        self.assertFalse(result.decision.allowed)
        self.assertEqual(result.strategy.name, "ask_clarification")
        self.assertEqual(result.block_reason, "project path without action verb")
