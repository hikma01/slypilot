from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from slypilot.classifier import Classification
from slypilot.intake import Intake
from slypilot.project_resolver import ResolvedProject
from slypilot.task_packet_builder import build_task_packet


class TaskPacketBuilderTests(TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def test_structured_dry_run_generates_packet(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "slypilot.cli", "corrige bug upload SlyScan", "--dry-run"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )

        output = result.stdout
        self.assertIn("SLYPILOT DRY RUN", output)
        self.assertIn("Detection:", output)
        self.assertIn("Generated Packet:", output)
        self.assertIn("--- TASK PACKET ---", output)

        packet_line = next(
            line for line in output.splitlines() if line.startswith("- slypilot/packets/generated/task_")
        )
        packet_rel_path = packet_line[2:].strip()
        packet_path = self.root / packet_rel_path
        self.assertTrue(packet_path.exists())

        content = packet_path.read_text(encoding="utf-8")
        self.assertIn("# TASK PACKET", content)
        self.assertIn("## METADATA", content)
        self.assertIn("## SYSTEM_FACTS", content)
        self.assertIn("## FORBIDDEN_ASSUMPTIONS", content)
        self.assertIn("## OUT_OF_SCOPE", content)
        self.assertIn("project: slyscan", content)
        self.assertIn("task_type: debug", content)
        self.assertIn("## NEGATIVE CONTEXT", content)
        self.assertIn("## EXPECTED OUTPUT", content)

        history_path = self.root / "slypilot" / "storage" / "history.jsonl"
        history_lines = [line for line in history_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertTrue(history_lines, "history.jsonl should contain at least one record after dry-run")
        payload = json.loads(history_lines[-1])
        self.assertEqual(payload["project"], "slyscan")
        self.assertEqual(payload["task_type"], "debug")
        self.assertEqual(payload["status"], "packet_generated")
        self.assertEqual(payload["prompt"], "corrige bug upload SlyScan")

    def test_missing_archi_ops_index_warns_instead_of_crashing(self) -> None:
        archi_ops_index = self.root / "archi_ops" / "index.md"
        backup = self.root / "archi_ops" / "index.md.bak"
        backup.write_text(archi_ops_index.read_text(encoding="utf-8"), encoding="utf-8")
        archi_ops_index.unlink()
        try:
            result = subprocess.run(
                [sys.executable, "-m", "slypilot.cli", "analyse architecture SlyPilot", "--dry-run"],
                cwd=self.root,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("Warnings:", result.stdout)
            self.assertIn("ARCHI OPS index missing", result.stdout)
        finally:
            archi_ops_index.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
            backup.unlink(missing_ok=True)

    def test_selected_foreign_project_paths_block_packet(self) -> None:
        intake = Intake(
            raw_request="analyse BarberExpert et identifie les bugs visibles",
            normalized_request="analyse BarberExpert et identifie les bugs visibles",
            repository_root=self.root,
        )
        classification = Classification(
            task_type="debug",
            project_hint="barberexpert",
            provider_hint="deepseek",
            environment_hint="local",
        )
        project = ResolvedProject(
            requested_project="barberexpert",
            name="barberexpert",
            provider="deepseek",
            environment="local",
            resolution_source="explicit_request",
            confidence="high",
            fallback_used=False,
            mismatch_detected=False,
        )

        foreign_result = type(
            "ForeignLoaderResult",
            (),
            {
                "files": [type("Item", (), {"path": "apps/api/src/routes/upload.mjs", "reason": "foreign", "content": "", "lines": 1})()],
                "maps": [],
                "metadata": {
                    "selected_lines_count": 1,
                    "estimated_raw_context_tokens": 20,
                    "files_excluded": 0,
                },
                "warnings": [],
            },
        )()

        with patch("slypilot.task_packet_builder.load_archi_ops_context", return_value=foreign_result):
            with self.assertRaises(ValueError):
                build_task_packet(intake, classification, project, self.root)


if __name__ == "__main__":
    import unittest

    unittest.main()
