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
            [sys.executable, "-m", "slypilot.cli"],
            cwd=self.root,
            input="analyse architecture SlyPilot\n",
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn('"task_type": "architecture"', result.stdout)
        self.assertIn('"project": "slypilot"', result.stdout)


if __name__ == "__main__":
    import unittest

    unittest.main()
