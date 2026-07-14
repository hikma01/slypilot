from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest import TestCase


class StructureTests(TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def test_repository_structure(self) -> None:
        expected_paths = [
            self.root / "README.md",
            self.root / "pyproject.toml",
            self.root / ".env.example",
            self.root / ".gitignore",
            self.root / "slypilot",
            self.root / "slypilot" / "cli.py",
            self.root / "slypilot" / "core",
            self.root / "slypilot" / "adapters",
            self.root / "slypilot" / "config",
            self.root / "slypilot" / "prompts",
            self.root / "slypilot" / "packets",
            self.root / "slypilot" / "storage",
            self.root / "slypilot" / "utils",
            self.root / "archi_ops",
            self.root / "archi_ops" / "index.md",
            self.root / "docs",
            self.root / "docs" / "02A_TASK_PACKET_RULES.md",
            self.root / "examples",
            self.root / "examples" / "task_packet_debug.md",
            self.root / "examples" / "task_packet_patch.md",
            self.root / "examples" / "task_packet_architecture.md",
            self.root / "examples" / "invalid",
            self.root / "examples" / "invalid" / "invalid_missing_metadata.md",
            self.root / "examples" / "invalid" / "invalid_no_negative_context.md",
            self.root / "examples" / "invalid" / "invalid_secret_exposed.md",
            self.root / "examples" / "invalid" / "invalid_token_budget.md",
            self.root / "schemas",
            self.root / "schemas" / "task_packet.schema.yaml",
            self.root / "tests",
        ]

        for path in expected_paths:
            self.assertTrue(path.exists(), f"Missing expected path: {path}")

    def test_documentation_inventory(self) -> None:
        docs = self.root / "docs"

        expected_docs = [
            "00_PROJECT_OVERVIEW.md",
            "01_ARCHITECTURE.md",
            "02_TASK_PACKET_STANDARD.md",
            "02A_TASK_PACKET_RULES.md",
            "03_ARCHI_OPS_INDEX.md",
            "04_SECURITY.md",
            "05_PROVIDER_ADAPTERS.md",
            "06_DEVELOPMENT_ROADMAP.md",
            "07_TESTING_STRATEGY.md",
            "08_DECISIONS_LOG.md",
            "09_METRICS_V1.md",
        ]

        for name in expected_docs:
            self.assertTrue((docs / name).exists(), f"Missing documentation file: {name}")

    def test_initial_detection_dry_run(self) -> None:
        cases = [
            ("corrige bug upload SlyScan", "slyscan"),
            ("analyse architecture SlyPilot", "slypilot"),
            ("explique problème login Hermes", "hermes"),
            ("corrige erreur API SlyScan", "slyscan"),
        ]

        for request, expected_project in cases:
            result = subprocess.run(
                [sys.executable, "-m", "slypilot.cli", "--dry-run", request],
                cwd=self.root,
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("Mode brouillon", result.stdout)
            self.assertIn(f"Projet détecté : {expected_project}", result.stdout)
            self.assertIn("Packet généré", result.stdout)


if __name__ == "__main__":
    import unittest

    unittest.main()
