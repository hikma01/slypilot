"""Project resolution for the initial detection pass."""

from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path

from slypilot.classifier import Classification
from slypilot.utils.rule_loader import load_rules


@dataclass(frozen=True)
class ResolvedProject:
    name: str
    provider: str
    environment: str
    requested_project: str = "unknown"
    resolution_source: str = "unknown"
    confidence: str = "low"
    fallback_used: bool = False
    mismatch_detected: bool = False


def resolve_project(
    classification: Classification,
    repository_root: Path,
    raw_request: str | None = None,
    current_working_directory: Path | None = None,
) -> ResolvedProject:
    if classification.task_type == "unknown":
        return ResolvedProject(
            requested_project="unknown",
            name="unknown",
            provider="deepseek",
            environment="local",
            resolution_source="technical_request_rejected",
            confidence="high",
            fallback_used=False,
            mismatch_detected=False,
        )

    rules = load_rules(repository_root / "projects.yaml")
    request_candidates = _detect_requested_projects(raw_request or "", rules, current_working_directory)
    cwd_project = _cwd_project_name(current_working_directory)
    local_project = _local_project_contract_name(current_working_directory)

    if len(request_candidates) > 1:
        chosen_project = request_candidates[0]
        return _build_resolved_project(
            requested_project="ambiguous",
            project_name=chosen_project,
            rules=rules,
            provider_hint=classification.provider_hint,
            environment_hint=classification.environment_hint,
            resolution_source="ambiguous_request",
            confidence="low",
            fallback_used=False,
            mismatch_detected=True,
        )

    if request_candidates:
        explicit_project = request_candidates[0]
        return _build_resolved_project(
            requested_project=explicit_project,
            project_name=explicit_project,
            rules=rules,
            provider_hint=classification.provider_hint,
            environment_hint=classification.environment_hint,
            resolution_source="explicit_request",
            confidence="high",
            fallback_used=False,
            mismatch_detected=False,
        )

    if cwd_project:
        return _build_resolved_project(
            requested_project=cwd_project,
            project_name=cwd_project,
            rules=rules,
            provider_hint=classification.provider_hint,
            environment_hint=classification.environment_hint,
            resolution_source="cwd",
            confidence="high",
            fallback_used=False,
            mismatch_detected=False,
        )

    if local_project:
        return _build_resolved_project(
            requested_project=local_project,
            project_name=local_project,
            rules=rules,
            provider_hint=classification.provider_hint,
            environment_hint=classification.environment_hint,
            resolution_source="local_project_yaml",
            confidence="medium",
            fallback_used=False,
            mismatch_detected=False,
        )

    project_name = str(rules["default_project"])
    return _build_resolved_project(
        requested_project=str(rules["default_project"]),
        project_name=project_name,
        rules=rules,
        provider_hint=classification.provider_hint,
        environment_hint=classification.environment_hint,
        resolution_source="global_index_fallback",
        confidence="low",
        fallback_used=True,
        mismatch_detected=False,
    )


def _build_resolved_project(
    requested_project: str,
    project_name: str,
    rules: dict[str, object],
    provider_hint: str | None,
    environment_hint: str | None,
    resolution_source: str,
    confidence: str,
    fallback_used: bool,
    mismatch_detected: bool,
) -> ResolvedProject:
    project = rules["projects"].get(project_name)
    if project is None:
        if fallback_used:
            project = rules["projects"][str(rules["default_project"])]
        else:
            return ResolvedProject(
                requested_project=requested_project,
                name=project_name,
                provider=provider_hint or "deepseek",
                environment=environment_hint or "local",
                resolution_source=resolution_source,
                confidence=confidence,
                fallback_used=fallback_used,
                mismatch_detected=mismatch_detected,
            )

    provider = provider_hint or project["provider"]
    environment = environment_hint or project["environment"]

    return ResolvedProject(
        requested_project=requested_project,
        name=project_name,
        provider=provider,
        environment=environment,
        resolution_source=resolution_source,
        confidence=confidence,
        fallback_used=fallback_used,
        mismatch_detected=mismatch_detected,
    )


def _detect_requested_projects(
    raw_request: str,
    rules: dict[str, object],
    current_working_directory: Path | None,
) -> list[str]:
    normalized = raw_request.lower()
    detected: list[str] = []

    for project_name, project_data in rules["projects"].items():
        aliases = [project_name, *project_data.get("aliases", [])]
        if any(_contains_token(normalized, alias.lower()) for alias in aliases):
            detected.append(project_name)

    if current_working_directory is not None:
        cwd_name = current_working_directory.name.strip().lower()
        if cwd_name and _contains_token(normalized, cwd_name) and cwd_name not in detected:
            detected.append(cwd_name)

    local_project = _local_project_contract_name(current_working_directory)
    if local_project and _contains_token(normalized, local_project) and local_project not in detected:
        detected.append(local_project)

    return detected


def _contains_token(text: str, candidate: str) -> bool:
    if not candidate:
        return False
    pattern = re.escape(candidate)
    return re.search(rf"(?<!\w){pattern}(?!\w)", text) is not None


def _cwd_project_name(current_working_directory: Path | None) -> str | None:
    if current_working_directory is None:
        return None
    cwd_name = current_working_directory.name.strip().lower()
    return cwd_name or None


def _local_project_contract_name(current_working_directory: Path | None) -> str | None:
    if current_working_directory is None:
        return None
    project_yaml = current_working_directory / "Documents" / "ARCHIOPS" / "project.yaml"
    if not project_yaml.exists():
        return None
    for raw_line in project_yaml.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("name:"):
            return stripped.split(":", 1)[1].strip().lower() or None
    return None
