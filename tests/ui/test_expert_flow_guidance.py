from __future__ import annotations

from unittest import TestCase

from slypilot.ui import (
    render_analysis_restitution,
    render_init_required_prompt,
    render_post_diagnostic_files,
    render_post_diagnostic_map,
    render_post_diagnostic_risks,
    render_post_diagnostic_stop,
)


class ExpertFlowGuidanceTests(TestCase):
    def test_init_prompt_is_recommendation_first(self) -> None:
        output = render_init_required_prompt("SlyAudit", "/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit")
        self.assertIn("Ma recommandation principale", output)
        self.assertIn("Pourquoi ?", output)
        self.assertIn("Alternatives :", output)
        self.assertIn("[1] Recommandé", output)
        self.assertIn("Réponds :", output)

    def test_analysis_restitution_uses_business_language(self) -> None:
        output = render_analysis_restitution(
            "SlyAudit",
            {
                "project_yaml_loaded": True,
                "project_contract_injected": True,
                "context_reduction_ratio": 3.0,
                "selected_maps": ["Documents/ARCHIOPS/repo-map.md"],
                "selected_files": ["src/app.py"],
                "negative_context": ["- no global scan"],
                "selection_reasons": ["src/app.py: task_relevance=selected"],
                "knowledge_contract": {
                    "repo_map": {
                        "path": "Documents/ARCHIOPS/repo-map.md",
                        "reason": "repo_structure",
                        "content": "# REPO MAP",
                    }
                },
            },
            "slypilot/packets/generated/task_123.md",
        )
        self.assertNotIn("packet", output.lower())
        self.assertIn("Vue d’ensemble", output)
        self.assertIn("Python (langage principal du projet)", output)
        self.assertIn("Ce que j'ai compris", output)
        self.assertIn("Ce que cela signifie", output)
        self.assertIn("Ce qui manque encore", output)
        self.assertIn("Ma recommandation", output)
        self.assertIn("Pourquoi", output)
        self.assertNotIn("Prochaine étape", output)

    def test_analysis_restitution_annotates_common_terms(self) -> None:
        output = render_analysis_restitution(
            "SlyAudit",
            {
                "project_yaml_loaded": True,
                "project_contract_injected": True,
                "context_reduction_ratio": 3.0,
                "selected_maps": ["Documents/ARCHIOPS/repo-map.md", "Documents/ARCHIOPS/runtime-map.md"],
                "selected_files": ["docker-compose.yml", "requirements.txt"],
                "negative_context": ["- no global scan"],
                "selection_reasons": ["docker-compose.yml: runtime_configuration"],
                "knowledge_contract": {
                    "repo_map": {
                        "path": "Documents/ARCHIOPS/repo-map.md",
                        "reason": "repo_structure",
                        "content": "# REPO MAP\n- docker-compose.yml\n- requirements.txt",
                    },
                    "runtime_map": {
                        "path": "Documents/ARCHIOPS/runtime-map.md",
                        "reason": "runtime_detection",
                        "content": "# RUNTIME MAP\n- Python\n- Docker",
                    },
                    "dependency_map": {
                        "path": "Documents/ARCHIOPS/dependency-map.md",
                        "reason": "dependency_surface",
                        "content": "# DEPENDENCY MAP\n- requirements.txt\n- docker-compose.yml",
                    },
                    "semantic_index": {
                        "path": "Documents/ARCHIOPS/semantic-index.md",
                        "reason": "semantic_surface",
                        "content": "# SEMANTIC INDEX\n- api\n- config\n- tests",
                    },
                    "important_files": [
                        {"path": "docker-compose.yml", "reason": "configuration runtime"},
                        {"path": "requirements.txt", "reason": "dépendances Python"},
                    ],
                },
            },
            "slypilot/packets/generated/task_123.md",
        )
        self.assertIn("Python (langage principal du projet)", output)
        self.assertIn("Docker (environnement isolé permettant d'exécuter le projet)", output)
        self.assertIn("docker-compose.yml (fichier qui décrit comment démarrer les composants du projet)", output)
        self.assertIn("requirements.txt (liste les bibliothèques Python utilisées)", output)

    def test_post_diagnostic_files_are_actionable(self) -> None:
        output = render_post_diagnostic_files(
            "SlyAudit",
            {
                "knowledge_contract": {
                    "important_files": [
                        {"path": "docker-compose.yml", "reason": "configuration runtime"},
                        {"path": "requirements.txt", "reason": "dépendances Python"},
                    ]
                }
            },
        )
        self.assertIn("Fichiers importants détectés", output)
        self.assertIn("docker-compose.yml", output)
        self.assertIn("requirements.txt", output)
        self.assertIn("Lecture possible", output)
        self.assertIn("Limite :", output)

    def test_post_diagnostic_map_is_readable(self) -> None:
        output = render_post_diagnostic_map(
            {
                "knowledge_contract": {
                    "repo_map": {"content": "# REPO MAP\n- docker-compose.yml\n- requirements.txt"},
                    "runtime_map": {"content": "# RUNTIME MAP\n- Python\n- Docker"},
                    "dependency_map": {"content": "# DEPENDENCY MAP\n- requirements.txt\n- docker-compose.yml"},
                },
                "selected_files": ["docker-compose.yml", "requirements.txt"],
            }
        )
        self.assertIn("Ce que je vois", output)
        self.assertIn("Ce que cela signifie", output)
        self.assertIn("Pourquoi c'est important", output)
        self.assertIn("Ce qui manque encore", output)
        self.assertIn("Ma recommandation", output)
        self.assertIn("Architecture simplifiée", output)
        self.assertIn("docker-compose.yml", output)
        self.assertIn("requirements.txt", output)
        self.assertIn("cartographie initiale", output)

    def test_post_diagnostic_risks_are_visible(self) -> None:
        output = render_post_diagnostic_risks(
            {
                "selection_reasons": ["cartographie encore initiale"],
                "negative_context": ["aucun scan global"],
            }
        )
        self.assertIn("Zones à risque visibles", output)
        self.assertIn("cartographie encore initiale", output)
        self.assertIn("Contexte borné", output)

    def test_post_diagnostic_stop_is_clear(self) -> None:
        output = render_post_diagnostic_stop()
        self.assertIn("Analyse arrêtée.", output)
        self.assertIn("Le contexte projet reste disponible dans cette session.", output)
