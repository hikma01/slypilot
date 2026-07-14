from __future__ import annotations

from unittest import TestCase

from slypilot.coordinator.coordinator_trace import ResourceTrace
from slypilot.ui import (
    render_banner,
    render_packet_summary,
)
from slypilot.ui import render_ambiguity_prompt, render_archiops_explanation, render_greeting_prompt, render_init_required_prompt, render_path_missing, render_sensitive_path


class ConsoleRendererTests(TestCase):
    def test_banner_is_french(self) -> None:
        output = render_banner()
        self.assertIn("Assistant de coordination technique", output)
        self.assertIn("Tape ta demande", output)

    def test_init_required_prompt_is_explanatory(self) -> None:
        output = render_init_required_prompt("SlyAudit", "/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit")
        self.assertIn("J'ai trouvé le dossier du projet", output)
        self.assertIn("[1] Recommandé", output)
        self.assertIn("[3]", output)

    def test_ambiguity_prompt_contains_example(self) -> None:
        output = render_ambiguity_prompt("SlyAudit", "/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit")
        self.assertIn("J'ai détecté une ressource locale", output)
        self.assertIn("1. analyser le projet", output)
        self.assertIn("2. initialiser ARCHI OPS", output)
        self.assertIn("3. afficher l’état du projet", output)

    def test_greeting_is_conversational(self) -> None:
        output = render_greeting_prompt()
        self.assertIn("Bonjour.", output)
        self.assertIn("Je peux t'aider", output)

    def test_explanation_and_path_messages(self) -> None:
        explanation = render_archiops_explanation("SlyAudit")
        missing = render_path_missing("/Users/hakimradi/Nextcloud/SlyProjet/FakeProject")
        blocked = render_sensitive_path("~/.ssh")
        self.assertIn("ARCHI OPS est la cartographie technique utilisée par SlyPilot.", explanation)
        self.assertIn("Le chemin fourni n'existe pas.", missing)
        self.assertIn("Accès refusé.", blocked)

    def test_packet_summary_is_verbose_and_separate(self) -> None:
        output = render_packet_summary(
            {
                "project_yaml_loaded": True,
                "project_yaml_path": "/tmp/project.yaml",
                "project_contract_injected": True,
                "selected_files_count": 2,
                "selected_lines_count": 120,
                "context_reduction_ratio": 14.2,
                "selected_maps": ["Documents/ARCHIOPS/repo-map.md"],
            }
        )
        self.assertIn("PACKET SUMMARY", output)
        self.assertIn("project_yaml_loaded: true", output)
        self.assertIn("selected_maps:", output)


if __name__ == "__main__":
    import unittest

    unittest.main()
