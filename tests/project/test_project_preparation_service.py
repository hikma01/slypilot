from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from slypilot.project import prepare_project


class ProjectPreparationServiceTests(TestCase):
    def test_prepare_project_creates_archiops_contract(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "src").mkdir()

            result = prepare_project(str(root))
            self.assertEqual(result.preparation_status, "success")
            self.assertTrue((root / "Documents" / "ARCHIOPS" / "project.yaml").exists())
            self.assertIn("project.yaml", "".join(result.created_files))

    def test_prepare_project_is_already_ready_when_contract_exists(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            archiops = root / "Documents" / "ARCHIOPS"
            archiops.mkdir(parents=True)
            (archiops / "project.yaml").write_text("project:\n  name: demo\n", encoding="utf-8")

            result = prepare_project(str(root))
            self.assertEqual(result.preparation_status, "already_ready")
            self.assertTrue((root / ".slypilot" / "project_memory.json").exists())
            self.assertTrue(result.created_files)

    def test_prepare_project_fails_for_missing_path(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            missing = Path(tmp_dir) / "missing"
            result = prepare_project(str(missing))
            self.assertEqual(result.preparation_status, "failed")
            self.assertTrue(result.errors)
