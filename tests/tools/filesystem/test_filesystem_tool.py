from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import TestCase

from slypilot.tools.filesystem import exists, is_dir, is_file, is_symlink, list_dir, read_text, stat


class FilesystemToolTests(TestCase):
    def test_exists_and_types(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            file_path = root / "sample.txt"
            file_path.write_text("hello", encoding="utf-8")
            self.assertTrue(exists(file_path))
            self.assertTrue(is_file(file_path))
            self.assertFalse(is_dir(file_path))
            self.assertFalse(is_symlink(file_path))
            self.assertTrue(stat(file_path)["exists"])

    def test_missing_path(self) -> None:
        self.assertFalse(exists("/tmp/does-not-exist-slypilot"))

    def test_list_dir_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "a").mkdir()
            (root / "a" / "b").mkdir()
            (root / "a" / "b" / "c.txt").write_text("x", encoding="utf-8")
            listing = list_dir(root, max_depth=1, max_entries=10)
            self.assertTrue(listing)
            self.assertLessEqual(len(listing), 10)
            self.assertTrue(any(Path(item).name == "a" for item in listing))

    def test_read_text_limited(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "large.txt"
            path.write_text("x" * 1000, encoding="utf-8")
            content = read_text(path, max_bytes=100)
            self.assertEqual(len(content), 100)


if __name__ == "__main__":
    import unittest

    unittest.main()
