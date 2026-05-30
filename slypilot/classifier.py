"""Deterministic first-pass request classifier."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from slypilot.intake import Intake
from slypilot.utils.rule_loader import load_rules


@dataclass(frozen=True)
class Classification:
    task_type: str
    project_hint: str | None
    provider_hint: str | None
    environment_hint: str | None


def classify_intake(intake: Intake, repository_root: Path) -> Classification:
    rules = load_rules(repository_root / "rules.yaml")
    request = intake.normalized_request.lower()

    task_type = "patch"
    for candidate in rules["task_type"]["ordered_rules"]:
        if any(keyword in request for keyword in candidate["keywords"]):
            task_type = candidate["task_type"]
            break

    project_hint = None
    provider_hint = None
    environment_hint = None
    for project_name in rules["project_order"]:
        project_data = rules["projects"][project_name]
        aliases = [project_name, *project_data["aliases"]]
        if any(alias in request for alias in aliases):
            project_hint = project_name
            provider_hint = project_data["provider"]
            environment_hint = project_data["environment"]
            break

    return Classification(
        task_type=task_type,
        project_hint=project_hint,
        provider_hint=provider_hint,
        environment_hint=environment_hint,
    )
