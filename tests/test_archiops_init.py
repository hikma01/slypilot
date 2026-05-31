from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import TestCase

from slypilot.archiops_init import initialize_project_with_index


class ArchiOpsInitTests(TestCase):
    def setUp(self) -> None:
        self.slypilot_root = Path(__file__).resolve().parents[1]

    def test_initialize_project_creates_minimal_archiops(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_repo, tempfile.TemporaryDirectory() as tmp_index:
            repo_root = Path(tmp_repo)
            index_path = Path(tmp_index) / "index.yaml"
            index_path.write_text(
                json.dumps({"version": 1, "projects": {}}, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            (repo_root / "README.md").write_text("# Demo\n", encoding="utf-8")
            (repo_root / "package.json").write_text('{"name":"demo"}\n', encoding="utf-8")
            (repo_root / "src").mkdir()
            (repo_root / "tests").mkdir()

            result = initialize_project_with_index(repo_root, index_path)

            archiops_dir = repo_root / "Documents" / "ARCHIOPS"
            self.assertTrue((archiops_dir / "project.yaml").exists())
            self.assertTrue((archiops_dir / "repo-map.md").exists())
            self.assertTrue((archiops_dir / "runtime-map.md").exists())
            self.assertTrue((archiops_dir / "dependency-map.md").exists())
            self.assertTrue((archiops_dir / "semantic-index.md").exists())
            self.assertEqual(result.project_name, repo_root.name.lower())
            self.assertEqual(result.updated_index, index_path)
            self.assertTrue(result.created_files)

            updated_index = json.loads(index_path.read_text(encoding="utf-8"))
            self.assertIn(repo_root.name.lower(), updated_index["projects"])
            project_entry = updated_index["projects"][repo_root.name.lower()]
            self.assertEqual(project_entry["status"], "initialized")
            self.assertEqual(project_entry["archiops_path"], "Documents/ARCHIOPS")
            self.assertTrue(any(item["path"] == "Documents/ARCHIOPS/runtime-map.md" for item in project_entry["maps"]))


if __name__ == "__main__":
    import unittest

    unittest.main()
