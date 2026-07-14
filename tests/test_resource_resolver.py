from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import TestCase

from slypilot.resource_resolver import resolve_resources


class ResourceResolverTests(TestCase):
    def test_detects_existing_project_directory(self) -> None:
        cwd = Path("/Users/hakimradi/Nextcloud/SlyProjet/SlyPilot")
        result = resolve_resources(
            "analyse mon projet slyaudit /Users/hakimradi/Nextcloud/SlyProjet/SlyAudit",
            cwd,
        )

        self.assertIn("/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit", result.detected_paths)
        self.assertIn("/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit", result.existing_paths)
        self.assertTrue(
            "project_directory" in result.resource_types or "archiops_project" in result.resource_types
        )
        self.assertIn(result.intake_status, {"init_required", "success"})
        self.assertEqual(result.selected_resource, "/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit")
        self.assertEqual(result.project_name, "slyaudit")
        self.assertTrue(result.warnings or result.intake_status == "success")

    def test_missing_path_is_reported(self) -> None:
        cwd = Path("/Users/hakimradi/Nextcloud/SlyProjet/SlyPilot")
        result = resolve_resources("analyse /Users/hakimradi/Nextcloud/SlyProjet/DoesNotExistSlyPilot", cwd)

        self.assertIn("/Users/hakimradi/Nextcloud/SlyProjet/DoesNotExistSlyPilot", result.missing_paths)
        self.assertEqual(result.intake_status, "missing_path")

    def test_inbox_shortcut_selects_inbox(self) -> None:
        cwd = Path("/Users/hakimradi/Nextcloud/SlyProjet/SlyPilot")
        inbox = cwd.parent / "SlyPilot" / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        result = resolve_resources("analyse la dernière capture dans l’inbox", cwd)

        self.assertEqual(result.intake_status, "success")
        self.assertEqual(result.selected_resource, str(inbox))


if __name__ == "__main__":
    import unittest

    unittest.main()
