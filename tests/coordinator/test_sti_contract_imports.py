from __future__ import annotations

from pathlib import Path
from unittest import TestCase

from slypilot.contracts import TechnicalBriefInvalid, TechnicalRequestBrief, TechnicalResponsePacket
from slypilot.coordinator.coordinator import handle_technical_brief
from slypilot.coordinator.technical_brief_builder import build_technical_brief


class STIContractImportTests(TestCase):
    def test_moved_technical_brief_builder_uses_shared_contracts(self) -> None:
        brief = build_technical_brief(
            "analyse",
            {"name": "SlyAudit", "path": "/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit"},
        )

        self.assertIsInstance(brief, TechnicalRequestBrief)
        self.assertEqual(brief.__class__.__module__, "slypilot.contracts")
        self.assertEqual(TechnicalResponsePacket.__module__, "slypilot.contracts")

    def test_technical_layer_raises_contract_error_without_project_path(self) -> None:
        brief = build_technical_brief("analyse", {"name": "SlyAudit", "path": ""})

        with self.assertRaises(TechnicalBriefInvalid):
            handle_technical_brief(brief, Path(__file__).resolve().parents[2], raw_request="analyse")

    def test_technical_brief_uses_brief_context_when_raw_message_is_natural_language(self) -> None:
        brief = build_technical_brief(
            "synthèse finale",
            {
                "name": "SlyAudit",
                "path": "/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit",
            },
        )

        packet = handle_technical_brief(
            brief,
            Path(__file__).resolve().parents[2],
            raw_request="voici mon projet /Users/hakimradi/Nextcloud/SlyProjet/SlyAudit",
        )

        self.assertEqual(packet.project_name, "SlyAudit")
        self.assertEqual(packet.project_path, "/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit")
        self.assertNotEqual(packet.project_name.lower(), "none")
