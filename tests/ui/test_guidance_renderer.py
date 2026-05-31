from __future__ import annotations

from unittest import TestCase

from slypilot.ui import (
    render_ambiguity_prompt,
    render_archiops_explanation,
    render_analysis_restitution,
    render_greeting_prompt,
    render_init_required_prompt,
    render_path_missing,
    render_sensitive_path,
)


class GuidanceRendererTests(TestCase):
    def test_greeting_is_conversational(self) -> None:
        output = render_greeting_prompt()
        self.assertIn("Bonjour.", output)
        self.assertIn("Je peux t'aider", output)

    def test_init_required_explains_why(self) -> None:
        output = render_init_required_prompt("SlyAudit", "/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit")
        self.assertIn("J'ai trouvé le dossier du projet", output)
        self.assertIn("Ma recommandation principale", output)
        self.assertIn("[1] Recommandé", output)
        self.assertIn("[I] Info", output)
        self.assertIn("Réponds :", output)

    def test_archiops_info_explains_concretely(self) -> None:
        output = render_archiops_explanation("SlyAudit")
        self.assertIn("ARCHI OPS est la cartographie technique utilisée par SlyPilot.", output)
        self.assertIn("project.yaml", output)

    def test_ambiguity_prompt_contains_choices(self) -> None:
        output = render_ambiguity_prompt("SlyAudit", "/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit")
        self.assertIn("J'ai détecté une ressource locale", output)
        self.assertIn("Ma recommandation principale", output)
        self.assertIn("1. analyser le projet", output)
        self.assertIn("2. initialiser ARCHI OPS", output)
        self.assertIn("3. afficher l’état du projet", output)

    def test_path_messages_are_human(self) -> None:
        missing = render_path_missing("/Users/hakimradi/Nextcloud/SlyProjet/FakeProject")
        blocked = render_sensitive_path("~/.ssh")
        self.assertIn("Le chemin fourni n'existe pas.", missing)
        self.assertIn("Accès refusé.", blocked)

    def test_analysis_restitution_is_readable(self) -> None:
        output = render_analysis_restitution(
            "SlyAudit",
            {
                "project_yaml_loaded": True,
                "project_contract_injected": True,
                "context_reduction_ratio": 12.5,
                "selected_maps": ["Documents/ARCHIOPS/repo-map.md", "Documents/ARCHIOPS/runtime-map.md"],
                "selected_files": ["src/app.py", "src/service.py"],
                "negative_context": ["- do not scan node_modules"],
                "selection_reasons": ["src/app.py: task_relevance=selected", "src/service.py: task_relevance=selected"],
            },
            "slypilot/packets/generated/task_123.md",
        )
        self.assertIn("Étapes réalisées", output)
        self.assertIn("Cartographie détectée", output)
        self.assertIn("Architecture globale", output)
        self.assertIn("Fichiers clés", output)
        self.assertIn("Dépendances principales", output)
        self.assertIn("Risques ou limites visibles", output)
        self.assertIn("Prochaine action recommandée", output)
