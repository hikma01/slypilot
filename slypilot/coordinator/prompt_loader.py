"""Load and assemble the coordinator prompt."""

from __future__ import annotations

from pathlib import Path


PROMPT_ORDER = [
    "identity.md",
    "responsibilities.md",
    "project_resolution.md",
    "ambiguity_management.md",
    "delegation_rules.md",
    "provider_selection.md",
    "guardrails.md",
    "output_contract.md",
]


def load_coordinator_prompt(prompts_root: Path) -> str:
    system_prompt = prompts_root / "system_prompt.md"
    if system_prompt.exists():
        return system_prompt.read_text(encoding="utf-8").strip()

    fragments: list[str] = []
    for filename in PROMPT_ORDER:
        path = prompts_root / filename
        if path.exists():
            fragments.append(path.read_text(encoding="utf-8").strip())

    prompt = "\n\n---\n\n".join(fragment for fragment in fragments if fragment)
    return prompt.strip()


def load_prompt_fragments(prompts_root: Path) -> list[str]:
    fragments: list[str] = []
    for filename in PROMPT_ORDER:
        path = prompts_root / filename
        if path.exists():
            fragments.append(path.read_text(encoding="utf-8").strip())
    return fragments
