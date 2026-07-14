from __future__ import annotations

from pathlib import Path
from unittest import TestCase

from slypilot.intake import build_intake
from slypilot.cognitive.cognitive_interface import CognitiveInterface
from slypilot.contracts import IntentType
from slypilot.resource_resolver import resolve_resources
from slypilot.coordinator.intent_analyzer import ANALYSIS_ACTION_TERMS, analyze_intent, resolve_intent_with_resource


class IntentAnalyzerTests(TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[2]
        self.cwd = Path("/Users/hakimradi/Nextcloud/SlyProjet/SlyPilot")

    def test_analysis_terms_include_verbs(self) -> None:
        self.assertIn("analyse", ANALYSIS_ACTION_TERMS)
        self.assertIn("verifie", ANALYSIS_ACTION_TERMS)
        self.assertIn("audite", ANALYSIS_ACTION_TERMS)

    def test_analyze_intent_detects_analysis_request(self) -> None:
        intake = build_intake("analyse mon projet /Users/hakimradi/Nextcloud/SlyProjet/SlyCRM", self.root)
        analysis = analyze_intent(intake, self.root)
        self.assertEqual(analysis.task_type, "patch")
        self.assertEqual(analysis.confidence, "high")

    def test_analyze_intent_is_case_insensitive(self) -> None:
        intake = build_intake("Analyse mon projet /Users/hakimradi/Nextcloud/SlyProjet/SlyCRM", self.root)
        analysis = analyze_intent(intake, self.root)
        self.assertEqual(analysis.task_type, "patch")
        self.assertEqual(analysis.confidence, "high")

    def test_resolve_intent_with_project_path_auto_prepares(self) -> None:
        intake = build_intake("analyse mon projet /Users/hakimradi/Nextcloud/SlyProjet/SlyCRM", self.root)
        resource = resolve_resources(intake.raw_request, self.cwd)
        fusion = resolve_intent_with_resource(intake, resource)
        self.assertEqual(fusion.detected_intent, "analyze_project")
        self.assertEqual(fusion.final_decision, "auto_prepare_then_analyze")
        self.assertFalse(fusion.ambiguity_reason)

    def test_path_only_requires_choice(self) -> None:
        intake = build_intake("/Users/hakimradi/Nextcloud/SlyProjet/SlyCRM", self.root)
        resource = resolve_resources(intake.raw_request, self.cwd)
        fusion = resolve_intent_with_resource(intake, resource)
        self.assertEqual(fusion.final_decision, "ask_project_action_choice")

    def test_analysis_without_path_asks_for_local_path(self) -> None:
        interface = CognitiveInterface(self.root)
        response = interface.qualify_intent("analyse", IntentType.TECHNICAL_REQUEST, None)

        self.assertIsInstance(response, str)
        self.assertIn("chemin local du projet", response)
        self.assertIn("analyse /Users/.../MonProjet", response)

    def test_path_only_stays_conversational_without_analysis_context(self) -> None:
        interface = CognitiveInterface(self.root)
        intent = interface.classify_intent("/Users/hakimradi/Nextcloud/SlyProjet/SlyCRM", None)
        response = interface.qualify_intent("/Users/hakimradi/Nextcloud/SlyProjet/SlyCRM", intent, None)

        self.assertEqual(intent, IntentType.HUMAN_QUESTION)
        self.assertIsInstance(response, str)
        self.assertIn("Avez-vous un dossier ou un projet spécifique à analyser ?", response)
