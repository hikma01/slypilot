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

        self.assertIn("Mode brouillon", result.stdout)
        self.assertIn("Packet généré", result.stdout)

    def test_stdin_request_works_without_args(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "slypilot.cli", "--dry-run"],
            cwd=self.root,
            input="analyse architecture SlyPilot\n",
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("Mode brouillon", result.stdout)
        self.assertIn("Projet détecté : slypilot", result.stdout)
        self.assertIn("Packet généré", result.stdout)

    def test_neutral_input_shows_human_refusal(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "slypilot.cli"],
            cwd=self.root,
            input="bonjour\n",
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("Bonjour.", result.stdout)
        self.assertIn("Je peux t'aider", result.stdout)
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
        self.assertIn("J'ai détecté une ressource locale", result.stdout)
        self.assertIn("Projet détecté :", result.stdout)
        self.assertIn("Alternatives :", result.stdout)
        self.assertIn("Choix conseillé :", result.stdout)
        self.assertIn("1. analyser le projet", result.stdout)


if __name__ == "__main__":
    import unittest

    unittest.main()
