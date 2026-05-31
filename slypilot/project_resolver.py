"""Project resolution for the initial detection pass."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from slypilot.classifier import Classification
from slypilot.utils.rule_loader import load_rules


@dataclass(frozen=True)
class ResolvedProject:
    name: str
    provider: str
    environment: str


def resolve_project(
    classification: Classification,
    repository_root: Path,
    raw_request: str | None = None,
    current_working_directory: Path | None = None,
) -> ResolvedProject:
    if classification.task_type == "unknown":
        return ResolvedProject(name="unknown", provider="deepseek", environment="local")

    rules = load_rules(repository_root / "projects.yaml")
    project_name = _resolve_project_name(classification, rules, raw_request, current_working_directory)
    project = rules["projects"].get(project_name, rules["projects"][rules["default_project"]])

    provider = classification.provider_hint or project["provider"]
    environment = classification.environment_hint or project["environment"]

    return ResolvedProject(
        name=project_name if project_name in rules["projects"] else project_name,
        provider=provider,
        environment=environment,
    )


def _resolve_project_name(
    classification: Classification,
    rules: dict[str, object],
    raw_request: str | None,
    current_working_directory: Path | None,
) -> str:
    if classification.project_hint:
        return classification.project_hint

    request = (raw_request or "").lower()
    if any(phrase in request for phrase in ("ce projet", "projet courant", "this project", "current project")):
        cwd_name = (current_working_directory or Path(os.getcwd())).name.strip().lower()
        if cwd_name:
            return cwd_name
        return "unknown_external"

    return str(rules["default_project"])
