from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import TestCase

from slypilot.cartography_service import generate_cartography


class CartographyServiceTests(TestCase):
    def test_bounded_scan_detects_top_level_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            (root / "package.json").write_text('{"name":"demo"}\n', encoding="utf-8")
            (root / "src").mkdir()
            (root / "tests").mkdir()
            (root / "node_modules").mkdir()
            (root / ".venv").mkdir()

            result = generate_cartography(root, "demo")

            top_level_section = result.repo_map.split("## EXCLUDED")[0]
            self.assertIn("README.md", top_level_section)
            self.assertIn("package.json", top_level_section)
            self.assertIn("src/", top_level_section)
            self.assertIn("tests/", top_level_section)
            self.assertNotIn("node_modules", top_level_section)
            self.assertNotIn(".venv", top_level_section)
            self.assertIn("node", result.detected_runtimes)
            self.assertIn("api", result.detected_domains)
            self.assertIn("tests", result.detected_domains)


if __name__ == "__main__":
    import unittest

    unittest.main()
