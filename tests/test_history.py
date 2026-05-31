from __future__ import annotations

import json
from pathlib import Path
from unittest import TestCase

from slypilot.history import latest_history_entry, read_history


class HistoryTests(TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.history_path = self.root / "slypilot" / "storage" / "history.test.jsonl"
        self.history_path.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.history_path.unlink(missing_ok=True)

    def test_read_history_returns_entries(self) -> None:
        self.history_path.write_text(
            "\n".join(
                [
                    json.dumps({"task_id": "task_1", "prompt": "one"}),
                    json.dumps({"task_id": "task_2", "prompt": "two"}),
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        entries = read_history(self.history_path)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["task_id"], "task_1")
        self.assertEqual(entries[1]["prompt"], "two")

    def test_latest_history_entry_returns_last(self) -> None:
        self.history_path.write_text(
            "\n".join(
                [
                    json.dumps({"task_id": "task_1"}),
                    json.dumps({"task_id": "task_2"}),
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        entry = latest_history_entry(self.history_path)
        self.assertIsNotNone(entry)
        assert entry is not None
        self.assertEqual(entry["task_id"], "task_2")


if __name__ == "__main__":
    import unittest

    unittest.main()
