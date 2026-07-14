from __future__ import annotations

from unittest import TestCase
from slypilot.ui.architecture_renderer import render_visual_architecture


class ArchitectureRendererTests(TestCase):
    def test_render_visual_architecture_python_docker(self) -> None:
        metadata = {
            "selected_files": ["docker-compose.yml", "main.py", "requirements.txt"],
            "knowledge_contract": {
                "runtime_map": {"content": "Project using Python 3.11"}
            }
        }
        output = render_visual_architecture("SlyAudit", metadata)

        self.assertIn("Projet SlyAudit", output)
        self.assertIn("├── Infrastructure", output)
        self.assertIn("├── Application", output)
        self.assertIn("├── Métier", output)
        self.assertIn("└── Tests", output)
        self.assertIn("Conseil du coordinateur", output)

    def test_render_visual_architecture_node(self) -> None:
        metadata = {
            "selected_files": ["package.json", "index.js"],
            "knowledge_contract": {
                "runtime_map": {"content": "Node.js environment"}
            }
        }
        output = render_visual_architecture("SlyNode", metadata)

        self.assertIn("Projet SlyNode", output)
        self.assertIn("├── Application", output)
        self.assertIn("Infrastructure", output)
