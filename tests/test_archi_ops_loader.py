from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

from slypilot.archi_ops_loader import load_archi_ops_context
from slypilot.classifier import Classification
from slypilot.intake import Intake
from slypilot.project_resolver import ResolvedProject
from slypilot.task_packet_builder import build_task_packet


class ArchiOpsLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def test_loader_is_deterministic(self) -> None:
        first = load_archi_ops_context(self.root, "slypilot", "architecture", "minimal")
        second = load_archi_ops_context(self.root, "slypilot", "architecture", "minimal")

        self.assertEqual([item.path for item in first.files], [item.path for item in second.files])
        self.assertEqual([item.path for item in first.maps], [item.path for item in second.maps])
        self.assertEqual(first.metadata["selected_files_count"], second.metadata["selected_files_count"])

    def test_loader_respects_profile_limits(self) -> None:
        result = load_archi_ops_context(self.root, "slyscan", "debug", "minimal")
        self.assertLessEqual(result.metadata["selected_files_count"], 3)
        self.assertLessEqual(result.metadata["selected_lines_count"], 200)

    def test_loader_warns_when_index_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "archi_ops").mkdir(parents=True)
            result = load_archi_ops_context(root, "slypilot", "architecture", "minimal")
            self.assertTrue(result.warnings)
            self.assertIn("ARCHI OPS index missing", result.warnings[0])
            self.assertEqual(result.metadata["files_selected"], 0)

    def test_packet_builder_includes_loader_selections(self) -> None:
        intake = Intake(
            raw_request="corrige bug upload SlyScan",
            normalized_request="corrige bug upload SlyScan",
            repository_root=self.root,
        )
        classification = Classification(
            task_type="debug",
            project_hint="slyscan",
            provider_hint="deepseek",
            environment_hint="local",
        )
        project = ResolvedProject(name="slyscan", provider="deepseek", environment="local")

        packet = build_task_packet(intake, classification, project, self.root)
        self.assertIn("selected_files:", packet.content)
        self.assertIn("selected_maps:", packet.content)
        self.assertIn("selection_reasons:", packet.content)
        self.assertIn("files_excluded_count:", packet.content)
        self.assertGreaterEqual(packet.metadata["selected_files_count"], 0)
        self.assertGreaterEqual(packet.metadata["selected_lines_count"], 0)

    def test_cli_dry_run_still_generates_packet(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "slypilot.cli", "corrige bug upload SlyScan", "--dry-run"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("SLYPILOT DRY RUN", result.stdout)
        self.assertIn("Generated Packet:", result.stdout)
        packet_line = next(
            line for line in result.stdout.splitlines() if line.startswith("- slypilot/packets/generated/task_")
        )
        packet_path = self.root / packet_line[2:].strip()
        self.assertTrue(packet_path.exists())
        content = packet_path.read_text(encoding="utf-8")
        self.assertIn("selected_maps:", content)
        self.assertIn("selection_reasons:", content)
        self.assertIn("files_excluded_count:", content)

    def test_mini_bench_reports_ratio_above_ten(self) -> None:
        cases = [
            "corrige bug upload SlyScan",
            "analyse architecture SlyPilot",
            "explique architecture SlyPilot",
        ]

        for request in cases:
            with self.subTest(request=request):
                result = subprocess.run(
                    [sys.executable, "-m", "slypilot.cli", request, "--dry-run"],
                    cwd=self.root,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                content = result.stdout
                ratio_line = next(
                    line for line in content.splitlines() if line.startswith("context_reduction_ratio:")
                )
                ratio = float(ratio_line.split(":", 1)[1].strip())
                self.assertGreater(ratio, 10.0)
                self.assertIn("selected_files_count:", content)
                self.assertIn("selected_lines_count:", content)
                self.assertIn("files_excluded_count:", content)


if __name__ == "__main__":
    unittest.main()
