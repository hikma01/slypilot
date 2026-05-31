from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import TestCase

from slypilot.tools.filesystem import classify_resource


class ResourceClassifierTests(TestCase):
    def test_detects_project_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "package.json").write_text("{}", encoding="utf-8")
            self.assertEqual(classify_resource(root).resource_type, "project_directory")

    def test_detects_git_repository(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / ".git").mkdir()
            self.assertEqual(classify_resource(root).resource_type, "git_repository")

    def test_detects_archiops_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            archiops = root / "Documents" / "ARCHIOPS"
            archiops.mkdir(parents=True)
            (archiops / "project.yaml").write_text("project:\n  name: demo\n", encoding="utf-8")
            self.assertEqual(classify_resource(root).resource_type, "archiops_project")

    def test_detects_file_types(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            md = root / "a.md"
            img = root / "a.png"
            pdf = root / "a.pdf"
            md.write_text("# doc", encoding="utf-8")
            img.write_bytes(b"png")
            pdf.write_bytes(b"%PDF")
            self.assertEqual(classify_resource(md).resource_type, "markdown_file")
            self.assertEqual(classify_resource(img).resource_type, "image_file")
            self.assertEqual(classify_resource(pdf).resource_type, "pdf_file")

    def test_detects_missing_path(self) -> None:
        self.assertEqual(classify_resource("/tmp/definitely-missing-slypilot").resource_type, "missing_path")


if __name__ == "__main__":
    import unittest

    unittest.main()
