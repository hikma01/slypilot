"""Project resolution for the initial detection pass."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from slypilot.classifier import Classification
from slypilot.utils.rule_loader import load_rules


@dataclass(frozen=True)
class ResolvedProject:
    name: str
    provider: str
    environment: str


def resolve_project(classification: Classification, repository_root: Path) -> ResolvedProject:
    rules = load_rules(repository_root / "projects.yaml")
    project_name = classification.project_hint or rules["default_project"]
    project = rules["projects"].get(project_name, rules["projects"][rules["default_project"]])

    provider = classification.provider_hint or project["provider"]
    environment = classification.environment_hint or project["environment"]

    return ResolvedProject(
        name=project_name,
        provider=provider,
        environment=environment,
    )
