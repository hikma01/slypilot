from __future__ import annotations

from pathlib import Path
from unittest import TestCase

from slypilot.coordinator.prompt_loader import load_coordinator_prompt, load_prompt_fragments


class PromptLoaderTests(TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[2]
        self.prompts_root = self.root / "prompts" / "coordinator"

    def test_prompt_fragments_are_loaded_in_order(self) -> None:
        fragments = load_prompt_fragments(self.prompts_root)

        self.assertGreaterEqual(len(fragments), 8)
        self.assertIn("SlyPilot Coordinator is the mandatory entry point.", fragments[0])
        self.assertIn("Return the resolved project, bounded context, trace, and execution decision.", fragments[-1])

    def test_system_prompt_is_loaded(self) -> None:
        prompt = load_coordinator_prompt(self.prompts_root)

        self.assertTrue(prompt.strip())
        self.assertIn("SlyPilot Coordinator — System Prompt", prompt)
        self.assertIn("requested_project != resolved_project", prompt)
        self.assertIn("COORDINATOR_TRACE", prompt)


if __name__ == "__main__":
    import unittest

    unittest.main()
