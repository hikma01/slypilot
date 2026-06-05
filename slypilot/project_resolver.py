"""Project resolution for the initial detection pass."""

from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path
from typing import Any

import yaml

from slypilot.classifier import Classification
from slypilot.utils.rule_loader import load_rules


@dataclass(frozen=True)
class ResolvedProject:
    name: str
    provider: str
    environment: str
    path: str = ""
    requested_project: str = "unknown"
    resolution_source: str = "unknown"
    confidence: str = "low"
    fallback_used: bool = False
    mismatch_detected: bool = False
    status: str = "success"  # success, needs_project_path, ambiguous

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "provider": self.provider,
            "environment": self.environment,
            "path": self.path,
            "requested_project": self.requested_project,
            "resolution_source": self.resolution_source,
            "confidence": self.confidence,
            "fallback_used": self.fallback_used,
            "mismatch_detected": self.mismatch_detected,
            "status": self.status,
        }


def resolve_project(
    classification: Classification,
    repository_root: Path,
    raw_request: str | None = None,
    current_working_directory: Path | None = None,
    resource_project_name: str | None = None,
    active_project_name: str | None = None,
    resource_path: str | None = None,
) -> ResolvedProject:
    # Fix: load_rules expects a file path, not a directory
    rules_path = repository_root / "projects.yaml"
    if not rules_path.exists():
        rules_path = repository_root / "rules.yaml"
    rules = load_rules(rules_path)
    known_projects = _load_known_projects(repository_root, rules)

    if classification.task_type == "unknown" and not (resource_path or resource_project_name or extract_explicit_unresolved_name(raw_request or "")):
        return ResolvedProject(
            name="none",
            provider="none",
            environment="none",
            path=resource_path or "",
            resolution_source="none",
            status="success",
        )

    explicit_candidates = _extract_explicit_project_candidates(raw_request or "", known_projects)
    unresolved_name = extract_explicit_unresolved_name(raw_request or "")

    if len(explicit_candidates) > 1:
        return ResolvedProject(
            name="ambiguous",
            provider="none",
            environment="none",
            path=resource_path or "",
            requested_project=_first_candidate(explicit_candidates, resource_project_name, unresolved_name),
            resolution_source="multiple_candidates",
            confidence="high",
            fallback_used=False,
            mismatch_detected=True,
            status="ambiguous",
        )

    if explicit_candidates:
        explicit_project = explicit_candidates[0]
        if resource_path or (resource_project_name and resource_project_name != "unknown"):
            resolution_source = "explicit_path"
        else:
            resolution_source = "explicit_request"
        return _build_resolved_project(
            requested_project=explicit_project,
            project_name=explicit_project,
            rules=rules,
            provider_hint=classification.provider_hint,
            environment_hint=classification.environment_hint,
            resolution_source=resolution_source,
            confidence="high",
            fallback_used=False,
            mismatch_detected=False,
            path=resource_path,
            project_catalog=known_projects,
        )

    if resource_project_name and resource_project_name != "unknown":
        resolution_source = "explicit_path"
        return _build_resolved_project(
            requested_project=resource_project_name,
            project_name=resource_project_name,
            rules=rules,
            provider_hint=classification.provider_hint,
            environment_hint=classification.environment_hint,
            resolution_source=resolution_source,
            confidence="high",
            fallback_used=False,
            mismatch_detected=False,
            path=resource_path,
            project_catalog=known_projects,
        )

    if unresolved_name:
        matched = _match_known_project(unresolved_name, known_projects)
        if matched:
            return _build_resolved_project(
                requested_project=unresolved_name,
                project_name=matched,
                rules=rules,
                provider_hint=classification.provider_hint,
                environment_hint=classification.environment_hint,
                resolution_source="explicit_request",
                confidence="high",
                fallback_used=False,
                mismatch_detected=False,
                path=resource_path,
                project_catalog=known_projects,
            )
        return ResolvedProject(
            name="unknown",
            provider="none",
            environment="none",
            path=resource_path or "",
            requested_project=unresolved_name,
            resolution_source="unresolved_name",
            status="needs_project_path",
        )

    if active_project_name:
        return _build_resolved_project(
            requested_project=active_project_name,
            project_name=active_project_name,
            rules=rules,
            provider_hint=classification.provider_hint,
            environment_hint=classification.environment_hint,
            resolution_source="session_context",
            confidence="high",
            fallback_used=False,
            mismatch_detected=False,
            path=resource_path,
            project_catalog=known_projects,
        )

    cwd_project_name = _detect_project_from_cwd(current_working_directory or Path.cwd(), known_projects)
    if cwd_project_name:
        return _build_resolved_project(
            requested_project=cwd_project_name,
            project_name=cwd_project_name,
            rules=rules,
            provider_hint=classification.provider_hint,
            environment_hint=classification.environment_hint,
            resolution_source="cwd",
            confidence="medium",
            fallback_used=False,
            mismatch_detected=False,
            path=str(current_working_directory or Path.cwd()),
            project_catalog=known_projects,
        )

    default_project_name = str(rules.get("default_project", "unknown"))
    return _build_resolved_project(
        requested_project=default_project_name,
        project_name=default_project_name,
        rules=rules,
        provider_hint=classification.provider_hint,
        environment_hint=classification.environment_hint,
        resolution_source="default_fallback",
        confidence="low",
        fallback_used=True,
        mismatch_detected=False,
        path=resource_path,
        project_catalog=known_projects,
    )


def extract_explicit_unresolved_name(request: str) -> str | None:
    # Look for "analyse X" where X is not a path
    match = re.search(r"(?:analyse|analyse de|analyse du|analyse le projet|analyse de projet)\s+([a-zA-Z0-9_\-]+)", request, re.IGNORECASE)
    if match:
        name = match.group(1)
        if name.lower() not in {"mon", "ce", "le", "un", "du", "de"}:
            return name
    return None


def _detect_project_from_cwd(cwd: Path, known_projects: dict[str, dict[str, Any]]) -> str | None:
    dirname = cwd.name.lower()
    if dirname in known_projects:
        return dirname

    for project_name, project_data in known_projects.items():
        root = str(project_data.get("root", "") or "").strip()
        if root and Path(root).expanduser().resolve() == cwd.expanduser().resolve():
            return project_name

    if (cwd / "Documents" / "ARCHIOPS").exists() or (cwd / "archi_ops").exists():
        project_yaml = cwd / "Documents" / "ARCHIOPS" / "project.yaml"
        if project_yaml.exists():
            try:
                with project_yaml.open(encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and data.get("project", {}).get("name"):
                        return str(data["project"]["name"]).lower()
            except Exception:
                pass
        return dirname

    return None


def _build_resolved_project(
    requested_project: str,
    project_name: str,
    rules: dict[str, Any],
    provider_hint: str | None,
    environment_hint: str | None,
    resolution_source: str,
    confidence: str,
    fallback_used: bool,
    mismatch_detected: bool,
    path: str | None = None,
    status: str = "success",
    project_catalog: dict[str, dict[str, Any]] | None = None,
) -> ResolvedProject:
    project_catalog = project_catalog or {}
    project_config = rules["projects"].get(project_name) or project_catalog.get(project_name)
    if project_config is None:
        if fallback_used:
            project_config = rules["projects"][str(rules["default_project"])]
        else:
            return ResolvedProject(
                requested_project=requested_project,
                name=project_name,
                provider=provider_hint or "deepseek",
                environment=environment_hint or "local",
                path=path or "",
                resolution_source=resolution_source,
                confidence=confidence,
                fallback_used=fallback_used,
                mismatch_detected=mismatch_detected,
                status=status
            )

    provider = provider_hint or project_config["provider"]
    environment = environment_hint or project_config["environment"]
    # If path not provided, use the one from rules if available
    final_path = path or project_config.get("path") or ""

    return ResolvedProject(
        requested_project=requested_project,
        name=project_name,
        provider=provider,
        environment=environment,
        path=str(final_path),
        resolution_source=resolution_source,
        confidence=confidence,
        fallback_used=fallback_used,
        mismatch_detected=mismatch_detected,
        status=status
    )


def is_likely_project_root(current_working_directory: Path) -> bool:
    """Check if the directory looks like a project root (has typical markers)."""
    markers = [
        "package.json",
        "requirements.txt",
        "pyproject.toml",
        "go.mod",
        "Cargo.toml",
        ".git",
        "Documents/ARCHIOPS",
        "rules.yaml",
    ]
    if any((current_working_directory / marker).exists() for marker in markers):
        return True
        
    soft_markers = [
        current_working_directory / "src",
        current_working_directory / "lib",
        current_working_directory / "app",
        current_working_directory / "apps",
        current_working_directory / "docs",
        current_working_directory / "tests",
    ]
    return any(marker.exists() for marker in soft_markers)


def _load_known_projects(repository_root: Path, rules: dict[str, Any]) -> dict[str, dict[str, Any]]:
    known: dict[str, dict[str, Any]] = {}
    rule_projects = rules.get("projects", {})
    if isinstance(rule_projects, dict):
        for project_name, project_data in rule_projects.items():
            if isinstance(project_data, dict):
                known[str(project_name).lower()] = dict(project_data)

    index_path = repository_root / "archi_ops" / "index.yaml"
    if index_path.exists():
        try:
            index_data = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
        except Exception:
            index_data = {}
        projects = index_data.get("projects", {}) if isinstance(index_data, dict) else {}
        if isinstance(projects, dict):
            for project_name, project_data in projects.items():
                if not isinstance(project_data, dict):
                    continue
                lowered = str(project_name).lower()
                known.setdefault(
                    lowered,
                    {
                        "provider": "deepseek",
                        "environment": "local",
                        "root": project_data.get("root", ""),
                    },
                )
                known[lowered].setdefault("root", project_data.get("root", ""))
                known[lowered].setdefault("provider", "deepseek")
                known[lowered].setdefault("environment", "local")
    return known


def _extract_explicit_project_candidates(request: str, known_projects: dict[str, dict[str, Any]]) -> list[str]:
    normalized_request = request.lower()
    matches: list[str] = []
    aliases: list[tuple[str, str]] = []
    for project_name, project_data in known_projects.items():
        aliases.append((project_name.lower(), project_name))
        raw_aliases = project_data.get("aliases", [])
        if isinstance(raw_aliases, list):
            for alias in raw_aliases:
                aliases.append((str(alias).lower(), project_name))

    aliases.sort(key=lambda item: len(item[0]), reverse=True)
    for alias, project_name in aliases:
        if not alias:
            continue
        if alias in normalized_request and project_name not in matches:
            matches.append(project_name)
    return matches


def _match_known_project(name: str, known_projects: dict[str, dict[str, Any]]) -> str | None:
    lowered = name.lower()
    if lowered in known_projects:
        return lowered
    for project_name, project_data in known_projects.items():
        aliases = [project_name, *[str(alias) for alias in project_data.get("aliases", []) if str(alias).strip()]]
        if any(alias.lower() == lowered for alias in aliases):
            return project_name
    return None


def _first_candidate(candidates: list[str], resource_project_name: str | None, unresolved_name: str | None) -> str:
    if resource_project_name and resource_project_name != "unknown":
        return resource_project_name
    if unresolved_name:
        return unresolved_name
    return candidates[0]
