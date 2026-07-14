from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from slypilot.runtime.conversation_loop import ConversationLoop


class PendingActionGuidanceTests(TestCase):
    def test_info_keeps_session_open_for_init_required(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            inputs = iter(["/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit", "info", "exit"])
            outputs: list[str] = []

            def fake_input(_: str) -> str:
                return next(inputs)

            fake_result = type(
                "Result",
                (),
                {
                    "intent": type("I", (), {"classification": type("C", (), {"task_type": "debug"})()})(),
                    "project": type("P", (), {"name": "slyaudit", "requested_project": "slyaudit", "resolution_source": "explicit_request", "status": "success"})(),
                    "resource": type(
                        "R",
                        (),
                        {
                            "intake_status": "init_required",
                            "detected_paths": ["/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit"],
                            "selected_resource": {
                                "path": "/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit",
                                "type": "project_directory",
                                "exists": True,
                                "policy_status": "allowed",
                            },
                            "to_dict": lambda self=None: {
                                "selected_resource": {
                                    "path": "/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit",
                                    "type": "project_directory",
                                    "exists": True,
                                    "policy_status": "allowed",
                                },
                                "intake_status": "init_required",
                                "detected_paths": ["/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit"],
                                "normalized_paths": ["/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit"],
                                "existing_paths": ["/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit"],
                                "missing_paths": [],
                                "blocked_paths": [],
                                "resource_types": ["project_directory"],
                            },
                        },
                    )(),
                    "decision": type("D", (), {"allowed": True, "reason": "approved"})(),
                    "trace": type(
                        "T",
                        (),
                        {
                            "to_dict": lambda self=None: {
                                "project": "slyaudit",
                                "intent_trace": {
                                    "raw_input": "analyse /Users/hakimradi/Nextcloud/SlyProjet/SlyAudit",
                                    "normalized_input": "analyse /users/hakimradi/nextcloud/slyprojet/slyaudit",
                                    "detected_action_terms": ["analyse"],
                                    "detected_intent": "analyze_project",
                                    "intent_confidence": 0.95,
                                    "detected_paths": ["/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit"],
                                    "resource_type": "project_directory",
                                    "project_name": "slyaudit",
                                    "fusion_result": "analysis_request_with_project_path",
                                    "final_decision": "auto_prepare_then_analyze",
                                    "ambiguity_reason": None,
                                },
                            }
                        },
                    )(),
                    "packet": type("PK", (), {"packet_path": Path("/tmp/packet.md"), "metadata": {"selected_maps": []}, "warnings": []})(),
                },
            )()

            with patch("slypilot.runtime.conversation_loop.coordinate_request", return_value=fake_result):
                loop = ConversationLoop(root, root, input_func=fake_input, output_func=outputs.append)
                code = loop.run()

        self.assertEqual(code, 0)
        joined = "\n".join(outputs)
        self.assertIn("ARCHI OPS est la cartographie technique utilisée par SlyPilot.", joined)
        self.assertIn("Que veux-tu faire ?", joined)
        self.assertIn("Que veux-tu faire ?", joined)
        self.assertIn("Session fermée.", joined)
