from __future__ import annotations

import io
import json
import os
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO
from unittest import mock, TestCase

import slypilot.cli
from slypilot.adapters.deepseek_adapter import DeepSeekAdapterError, run_deepseek_live
from slypilot.classifier import Classification
from slypilot.intake import Intake
from slypilot.project_resolver import ResolvedProject
from slypilot.task_packet_builder import build_task_packet


class DeepSeekAdapterTests(TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.intake = Intake(
            raw_request="corrige bug upload SlyScan",
            normalized_request="corrige bug upload SlyScan",
            repository_root=self.root,
        )
        self.classification = Classification(
            task_type="debug",
            project_hint="slyscan",
            provider_hint="deepseek",
            environment_hint="local",
        )
        self.project = ResolvedProject(name="slyscan", provider="deepseek", environment="local")
        self.packet = build_task_packet(self.intake, self.classification, self.project, self.root)

    def test_missing_api_key_raises_clean_error(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(DeepSeekAdapterError):
                run_deepseek_live(self.packet)

    def test_live_run_parses_response(self) -> None:
        payload = {
            "choices": [
                {
                    "message": {
                        "content": "Diagnostic: upload boundary failed."
                    }
                }
            ]
        }

        class FakeResponse(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        fake_response = FakeResponse(json.dumps(payload).encode("utf-8"))

        with mock.patch.dict(
            os.environ,
            {"DEEPSEEK_API_KEY": "test-key", "DEEPSEEK_BASE_URL": "https://api.deepseek.com"},
            clear=True,
        ):
            with mock.patch("slypilot.adapters.deepseek_adapter.request.urlopen", return_value=fake_response) as mocked_urlopen:
                response = run_deepseek_live(self.packet)

        self.assertEqual(response.provider, "deepseek")
        self.assertEqual(response.status, "completed")
        self.assertEqual(response.response_text, "Diagnostic: upload boundary failed.")
        self.assertGreaterEqual(response.response_tokens, 1)
        self.assertTrue(mocked_urlopen.called)

    def test_history_accepts_live_run_metadata(self) -> None:
        history_path = self.root / "slypilot" / "storage" / "history.jsonl"
        before = history_path.read_text(encoding="utf-8") if history_path.exists() else ""
        try:
            payload = {
                "choices": [
                    {
                        "message": {
                            "content": "OK"
                        }
                    }
                ]
            }

            class FakeResponse(io.BytesIO):
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

            with mock.patch.dict(
                os.environ,
                {"DEEPSEEK_API_KEY": "test-key", "DEEPSEEK_BASE_URL": "https://api.deepseek.com"},
                clear=True,
            ):
                with mock.patch(
                    "slypilot.adapters.deepseek_adapter.request.urlopen",
                    return_value=FakeResponse(json.dumps(payload).encode("utf-8")),
                ):
                    stdout = StringIO()
                    with redirect_stdout(stdout):
                        exit_code = slypilot.cli.main(["corrige bug upload SlyScan", "--live-run"])

            self.assertEqual(exit_code, 0)
            self.assertIn("Mode exécution", stdout.getvalue())
            self.assertIn("Réponse fournisseur :", stdout.getvalue())
            self.assertIn("Métriques :", stdout.getvalue())
        finally:
            if history_path.exists():
                history_path.write_text(before, encoding="utf-8")
