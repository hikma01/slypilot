from __future__ import annotations

from pathlib import Path
from unittest import TestCase

from slypilot.tools.filesystem import detect_paths


class PathDetectorTests(TestCase):
    def setUp(self) -> None:
        self.cwd = Path("/Users/hakimradi/Nextcloud/SlyProjet/SlyPilot")

    def test_detects_absolute_and_relative_paths(self) -> None:
        request = "analyse /Users/hakimradi/Nextcloud/SlyProjet/SlyAudit et ./docs"
        paths = detect_paths(request, self.cwd)
        self.assertTrue(any(item.raw_path.startswith("/Users/") for item in paths))
        self.assertTrue(any(item.raw_path.startswith("./") for item in paths))

    def test_detects_home_path(self) -> None:
        paths = detect_paths("analyse ~/Documents", self.cwd)
        self.assertTrue(paths)
        self.assertTrue(paths[0].normalized_path)

    def test_ignores_plain_text(self) -> None:
        self.assertEqual(detect_paths("bonjour merci", self.cwd), [])

    def test_detects_multiple_paths(self) -> None:
        paths = detect_paths("compare /Users/hakimradi/Nextcloud /Users/hakimradi/Desktop", self.cwd)
        self.assertGreaterEqual(len(paths), 2)


if __name__ == "__main__":
    import unittest

    unittest.main()
