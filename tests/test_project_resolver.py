from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest import TestCase

from slypilot.classifier import Classification
from slypilot.project_resolver import resolve_project


class ProjectResolverTests(TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.barberexpert_root = Path("/Users/hakimradi/Nextcloud/SlyProjet/BarberExpert")

    def test_contextual_request_uses_current_directory(self) -> None:
        classification = Classification(
            task_type="debug",
            project_hint=None,
            provider_hint=None,
            environment_hint=None,
        )

        resolved = resolve_project(
            classification,
            self.root,
            raw_request="analyse ce projet si tu trouves des bugs",
            current_working_directory=self.barberexpert_root,
        )

        self.assertEqual(resolved.name, "barberexpert")
        self.assertEqual(resolved.provider, "deepseek")
        self.assertEqual(resolved.environment, "local")

    def test_explicit_project_still_wins(self) -> None:
        classification = Classification(
            task_type="debug",
            project_hint="slyscan",
            provider_hint=None,
            environment_hint=None,
        )

        resolved = resolve_project(
            classification,
            self.root,
            raw_request="analyse ce projet",
            current_working_directory=self.barberexpert_root,
        )

        self.assertEqual(resolved.name, "slyscan")

    def test_cli_dry_run_in_barberexpert_uses_contextual_project(self) -> None:
        result = subprocess.run(
            [str(self.root / "bin" / "slypilot"), "--dry-run", "analyse ce projet si tu trouves des bugs"],
            cwd=self.barberexpert_root,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("- project: barberexpert", result.stdout)
        self.assertIn("ARCHI OPS project not indexed: barberexpert", result.stdout)
        self.assertNotIn("- project: slyscan", result.stdout)


if __name__ == "__main__":
    import unittest

    unittest.main()
