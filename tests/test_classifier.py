from __future__ import annotations

import json
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
                [sys.executable, "-m", "slypilot.cli", request],
                cwd=self.root,
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(result.stdout)
            self.assertEqual(payload["task_type"], "unknown")
            self.assertEqual(payload["project"], "unknown")
            self.assertEqual(payload["status"], "needs_technical_request")

    def test_technical_requests_remain_classified(self) -> None:
        cases = [
            ("analyse architecture SlyPilot", {"task_type": "architecture", "project": "slypilot"}),
            ("corrige bug upload SlyScan", {"task_type": "debug", "project": "slyscan"}),
            ("explique problème login Hermes", {"task_type": "explain", "project": "hermes"}),
            ("ajoute test history", {"task_type": "patch", "project": "slyscan"}),
            ("fix cli launcher", {"task_type": "patch", "project": "slyscan"}),
        ]

        for request, expected in cases:
            result = subprocess.run(
                [sys.executable, "-m", "slypilot.cli", request],
                cwd=self.root,
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(result.stdout)
            self.assertEqual(payload["task_type"], expected["task_type"])
            self.assertEqual(payload["project"], expected["project"])


if __name__ == "__main__":
    import unittest

    unittest.main()
