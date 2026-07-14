from __future__ import annotations

from unittest import TestCase

from slypilot.coordinator.expert_interpreter import interpret_expert_diagnostic


class ExpertInterpreterTests(TestCase):
    def test_interprets_technical_maps_into_advice(self) -> None:
        diagnostic = interpret_expert_diagnostic(
            "SlyAudit",
            {
                "selected_maps": [
                    "Documents/ARCHIOPS/repo-map.md",
                    "Documents/ARCHIOPS/runtime-map.md",
                    "Documents/ARCHIOPS/dependency-map.md",
                    "Documents/ARCHIOPS/semantic-index.md",
                ],
                "selected_files": ["docker-compose.yml", "requirements.txt"],
                "negative_context": ["- no global scan", "- no provider call"],
                "selection_reasons": [
                    "docker-compose.yml: runtime_configuration",
                    "requirements.txt: python_dependencies",
                    "cartographie encore initiale",
                ],
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
        )

        self.assertIn("Python", diagnostic.detected_technologies)
        self.assertIn("Docker", diagnostic.detected_technologies)
        self.assertIn("docker-compose.yml", diagnostic.detected_files)
        self.assertIn("requirements.txt", diagnostic.detected_files)
        self.assertIn("api", diagnostic.detected_domains)
        self.assertTrue(diagnostic.summary)
        self.assertTrue(diagnostic.understood)
        self.assertTrue(diagnostic.meaning)
        self.assertTrue(diagnostic.missing)
        self.assertIn("Explorer l'arborescence métier", diagnostic.recommendation)
        self.assertTrue(diagnostic.why)
        self.assertIn("1 — analyser les fichiers importants", diagnostic.next_step[0])
