from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from unittest import TestCase


class CliLauncherTests(TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.launcher = self.root / "bin" / "slypilot"

    def test_launcher_script_exists(self) -> None:
        self.assertTrue(self.launcher.exists())
        self.assertTrue(os.access(self.launcher, os.X_OK))

    def test_launcher_help_works(self) -> None:
        result = subprocess.run(
            [str(self.launcher), "--help"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("usage: slypilot", result.stdout)

    def test_launcher_dry_run_works(self) -> None:
        result = subprocess.run(
            [str(self.launcher), "--dry-run", "analyse architecture SlyPilot"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("SLYPILOT DRY RUN", result.stdout)
        self.assertIn("Generated Packet:", result.stdout)

    def test_stdin_request_works_without_args(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "slypilot.cli", "--dry-run"],
            cwd=self.root,
            input="analyse architecture SlyPilot\n",
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("SLYPILOT DRY RUN", result.stdout)
        self.assertIn("task_type: architecture", result.stdout)
        self.assertIn("project: slypilot", result.stdout)

    def test_neutral_input_shows_human_refusal(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "slypilot.cli"],
            cwd=self.root,
            input="bonjour\n",
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("SlyPilot attend une tâche technique.", result.stdout)
        self.assertIn("Exemples :", result.stdout)
        self.assertNotIn("task_type", result.stdout)
        self.assertNotIn("project", result.stdout)
        self.assertNotIn("needs_technical_request", result.stdout)

    def test_ambiguous_project_path_shows_reformulation_example(self) -> None:
        result = subprocess.run(
            [str(self.launcher), "--dry-run", "analyse /Users/hakimradi/Nextcloud/SlyProjet/SlyAudit et /Users/hakimradi/Nextcloud/SlyProjet/SlyPilot"],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Commande comprise partiellement :", result.stdout)
        self.assertIn("- ressource détectée :", result.stdout)
        self.assertIn("Reformule par exemple :", result.stdout)
        self.assertIn("analyse le projet", result.stdout)


if __name__ == "__main__":
    import unittest

    unittest.main()
