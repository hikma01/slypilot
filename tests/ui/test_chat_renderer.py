from __future__ import annotations

from unittest import TestCase

from slypilot.ui import render_slypilot_message, render_user_message


class ChatRendererTests(TestCase):
    def test_user_message_is_rendered_in_french(self) -> None:
        output = render_user_message("analyse le projet")
        self.assertIn("👤 Utilisateur", output)
        self.assertIn("analyse le projet", output)

    def test_slypilot_message_is_rendered(self) -> None:
        output = render_slypilot_message("SlyPilot", ["Projet détecté :", "SlyAudit"])
        self.assertIn("🤖 SlyPilot", output)
        self.assertIn("Projet détecté", output)
        self.assertIn("SlyAudit", output)

    def test_slypilot_message_without_header(self) -> None:
        output = render_slypilot_message("Diagnostic", ["Détails"], include_header=False)
        self.assertNotIn("🤖 SlyPilot", output)
        self.assertIn("Diagnostic", output)

    def test_technical_info_rendering(self) -> None:
        from slypilot.ui.chat_renderer import render_technical_info
        output = render_technical_info("Info technique")
        self.assertNotIn("🤖 SlyPilot", output)
        self.assertIn("› Info technique", output)


if __name__ == "__main__":
    import unittest

    unittest.main()
