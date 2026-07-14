from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import slypilot.cli as cli
from slypilot.runtime.session_registry import SessionRegistry
from slypilot.runtime.session_resume import resume_last_session
from slypilot.runtime.session_store import SessionStore


class CliRuntimeCommandsTests(TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def test_sessions_command_lists_sessions(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            registry = SessionRegistry(root)
            registry.upsert_session(
                session_id="s1",
                created_at="2026-05-31T15:00:01+00:00",
                last_activity="2026-05-31T15:08:32+00:00",
                project="slyaudit",
                status="closed",
                message_count=14,
                cwd="/tmp/demo",
            )
            output = cli._render_sessions_list(root)
            self.assertIn("📚 Sessions", output)
            self.assertIn("s1", output)

    def test_history_command_lists_recent_sessions(self) -> None:
        output = cli._render_history(self.root)
        self.assertIn("Historique récent", output)

    def test_resume_last_command_runs(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            registry = SessionRegistry(root)
            store = SessionStore(root / "runtime" / "sessions")
            store.append("s1", {"role": "user", "content": "bonjour"})
            store.append("s1", {"role": "assistant", "content": "salut"})
            registry.upsert_session(
                session_id="s1",
                created_at="2026-05-31T15:00:01+00:00",
                last_activity="2026-05-31T15:08:32+00:00",
                project="slyaudit",
                status="closed",
                message_count=2,
                cwd="/tmp/demo",
            )
            data = resume_last_session(root)
            self.assertEqual(data["session"]["session_id"], "s1")
            self.assertEqual(len(data["events"]), 2)
