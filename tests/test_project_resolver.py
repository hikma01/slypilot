from __future__ import annotations

import subprocess
import sys
import tempfile
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

    def test_contextual_request_prefers_current_directory_over_default(self) -> None:
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

        self.assertEqual(resolved.name, "barberexpert")
        self.assertEqual(resolved.resolution_source, "cwd")
        self.assertFalse(resolved.fallback_used)

    def test_absolute_path_request_does_not_confuse_home_directory_as_project(self) -> None:
        classification = Classification(
            task_type="debug",
            project_hint=None,
            provider_hint=None,
            environment_hint=None,
        )

        resolved = resolve_project(
            classification,
            self.root,
            raw_request="Analyse mon projet /Users/hakimradi/Nextcloud/SlyProjet/SlyAudit",
            current_working_directory=Path.home(),
            resource_project_name="slyaudit",
        )

        self.assertEqual(resolved.name, "slyaudit")
        self.assertEqual(resolved.resolution_source, "explicit_path")
        self.assertFalse(resolved.mismatch_detected)

    def test_explicit_barberexpert_wins(self) -> None:
        classification = Classification(
            task_type="debug",
            project_hint=None,
            provider_hint=None,
            environment_hint=None,
        )

        resolved = resolve_project(
            classification,
            self.root,
            raw_request="analyse BarberExpert et identifie les bugs visibles",
            current_working_directory=self.barberexpert_root,
        )

        self.assertEqual(resolved.name, "barberexpert")
        self.assertEqual(resolved.resolution_source, "explicit_request")
        self.assertFalse(resolved.fallback_used)

    def test_explicit_slyscan_wins(self) -> None:
        classification = Classification(
            task_type="debug",
            project_hint=None,
            provider_hint=None,
            environment_hint=None,
        )

        resolved = resolve_project(
            classification,
            self.root,
            raw_request="analyse SlyScan et identifie les bugs visibles",
            current_working_directory=self.barberexpert_root,
        )

        self.assertEqual(resolved.name, "slyscan")
        self.assertEqual(resolved.resolution_source, "explicit_request")
        self.assertFalse(resolved.mismatch_detected)

    def test_cli_dry_run_in_barberexpert_uses_contextual_project(self) -> None:
        result = subprocess.run(
            [str(self.root / "bin" / "slypilot"), "--dry-run", "--verbose", "analyse ce projet si tu trouves des bugs"],
            cwd=self.barberexpert_root,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("Projet détecté : barberexpert", result.stdout)
        self.assertIn("PACKET SUMMARY", result.stdout)
        self.assertIn("project_yaml_loaded: true", result.stdout)
        self.assertIn("project_yaml_path: /Users/hakimradi/Nextcloud/SlyProjet/BarberExpert/Documents/ARCHIOPS/project.yaml", result.stdout)
        self.assertIn("project_contract_injected: true", result.stdout)
        self.assertIn("dry_run          : true", result.stdout)
        self.assertIn("live_run         : false", result.stdout)
        self.assertIn("provider_called  : false", result.stdout)
        self.assertIn("Mode brouillon", result.stdout)
        self.assertIn("Packet généré", result.stdout)
        self.assertIn("Documents/ARCHIOPS/runtime-map.md", result.stdout)
        self.assertIn("Documents/ARCHIOPS/dependency-map.md", result.stdout)
        self.assertIn("Documents/ARCHIOPS/semantic-index.md", result.stdout)
        self.assertNotIn("- project: slyscan", result.stdout)

    def test_missing_project_yaml_emits_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_repo:
            repo_root = Path(tmp_repo)
            (repo_root / "README.md").write_text("# Demo\n", encoding="utf-8")
            (repo_root / "package.json").write_text('{"name":"demo"}\n', encoding="utf-8")
            (repo_root / "src").mkdir()

            result = subprocess.run(
                [str(self.root / "bin" / "slypilot"), "--dry-run", "--verbose", "analyse ce projet si tu trouves des bugs"],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("Avertissements :", result.stdout)
            self.assertIn("ARCHI OPS project contract missing:", result.stdout)
            self.assertIn("project_yaml_loaded: false", result.stdout)
            self.assertIn("project_contract_injected: false", result.stdout)

    def test_ambiguous_request_blocks_confirmation(self) -> None:
        result = subprocess.run(
            [str(self.root / "bin" / "slypilot"), "--dry-run", "--verbose", "analyse SlyScan et BarberExpert"],
            cwd=self.barberexpert_root,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("J'ai détecté une ressource locale", result.stdout)
        self.assertIn("Alternatives :", result.stdout)
        self.assertIn("Choix conseillé :", result.stdout)
        self.assertIn("1. analyser le projet", result.stdout)


if __name__ == "__main__":
    import unittest

    unittest.main()
