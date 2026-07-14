from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest import TestCase


class ClassifierTests(TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def test_neutral_requests_are_unknown(self) -> None:
        cases = ["bonjour", "salut", "merci", "ok", "ça va ?"]

        for request in cases:
            result = subprocess.run(
                [sys.executable, "-m", "slypilot.cli", "--dry-run", request],
                cwd=self.root,
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("Bonjour.", result.stdout)
            self.assertIn("Je peux t'aider", result.stdout)
            self.assertNotIn("task_type", result.stdout)
            self.assertNotIn("project", result.stdout)
            self.assertNotIn("needs_technical_request", result.stdout)

    def test_technical_requests_remain_classified(self) -> None:
        cases = [
            ("analyse architecture SlyPilot", {"task_type": "architecture", "project": "slypilot"}),
            ("corrige bug upload SlyScan", {"task_type": "debug", "project": "slyscan"}),
            ("explique problème login Hermes", {"task_type": "explain", "project": "hermes"}),
            ("ajoute test history", {"task_type": "patch", "project": "slypilot"}),
            ("fix cli launcher", {"task_type": "patch", "project": "slypilot"}),
        ]

        for request, expected in cases:
            result = subprocess.run(
                [sys.executable, "-m", "slypilot.cli", "--dry-run", request],
                cwd=self.root,
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("Mode brouillon", result.stdout)
            self.assertIn(f"Projet détecté : {expected['project']}", result.stdout)
            self.assertNotIn("needs_technical_request", result.stdout)


if __name__ == "__main__":
    import unittest

    unittest.main()
