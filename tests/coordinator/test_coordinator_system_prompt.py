from __future__ import annotations

from pathlib import Path
from unittest import TestCase

from slypilot.coordinator import coordinate_request
from slypilot.intake import build_intake


class CoordinatorSystemPromptTests(TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[2]
        self.barberexpert_root = Path("/Users/hakimradi/Nextcloud/SlyProjet/BarberExpert")

    def test_system_prompt_is_loaded_into_result(self) -> None:
        intake = build_intake("analyse BarberExpert et identifie les bugs visibles", self.root)
        result = coordinate_request(
            intake,
            self.root,
            current_working_directory=self.barberexpert_root,
            dry_run=True,
        )

        self.assertTrue(result.system_prompt.strip())
        self.assertIn("SlyPilot Coordinator — System Prompt", result.system_prompt)
        self.assertIn("requested_project != resolved_project", result.system_prompt)
        self.assertIn("COORDINATOR_TRACE", result.system_prompt)

    def test_system_prompt_is_not_empty_for_generic_requests(self) -> None:
        intake = build_intake("analyse le projet courant et identifie les bugs visibles sans scan profond", self.root)
        result = coordinate_request(
            intake,
            self.root,
            current_working_directory=self.barberexpert_root,
            dry_run=True,
        )

        self.assertTrue(result.system_prompt)


if __name__ == "__main__":
    import unittest

    unittest.main()
