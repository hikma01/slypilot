"""Minimal YAML loader for the local rule files.

The repository intentionally avoids adding a runtime dependency for YAML parsing
in this V1 foundation. The files in use are small and constrained enough for a
deterministic line-based parser.
"""

from __future__ import annotations

from pathlib import Path


def load_rules(path: Path) -> dict[str, object]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if any(line.startswith("default_project:") for line in lines):
        return _parse_projects(lines)
    return _parse_classifier_rules(lines)


def _parse_projects(lines: list[str]) -> dict[str, object]:
    default_project = ""
    projects: dict[str, dict[str, object]] = {}
    current_project = None
    current_list_key = None

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("default_project:"):
            default_project = stripped.split(":", 1)[1].strip()
            continue
        if stripped.endswith(":") and not line.startswith("  "):
            key = stripped[:-1]
            if key != "projects":
                current_project = key
                projects.setdefault(current_project, {})
            continue
        if current_project is None and stripped == "projects:":
            continue
        if stripped.endswith(":") and line.startswith("  ") and current_project is None:
            current_project = stripped[:-1]
            projects.setdefault(current_project, {})
            continue
        if current_project is None:
            continue
        if stripped.startswith("aliases:"):
            current_list_key = "aliases"
            projects[current_project][current_list_key] = []
            continue
        if stripped.startswith("provider:"):
            projects[current_project]["provider"] = stripped.split(":", 1)[1].strip()
            continue
        if stripped.startswith("environment:"):
            projects[current_project]["environment"] = stripped.split(":", 1)[1].strip()
            continue
        if stripped.startswith("- ") and current_list_key == "aliases":
            projects[current_project]["aliases"].append(stripped[2:].strip())

    return {"default_project": default_project, "projects": projects}


def _parse_classifier_rules(lines: list[str]) -> dict[str, object]:
    debug_keywords: list[str] = []
    current_section = None
    current_project = None
    projects: dict[str, dict[str, object]] = {}

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.endswith(":") and not line.startswith("  "):
            current_section = stripped[:-1]
            continue
        if current_section == "task_type" and stripped.startswith("debug_keywords:"):
            continue
        if current_section == "task_type" and stripped.startswith("- "):
            debug_keywords.append(stripped[2:].strip())
            continue
        if current_section == "projects" and stripped.endswith(":"):
            current_project = stripped[:-1]
            projects.setdefault(current_project, {"aliases": []})
            continue
        if current_section == "projects" and current_project:
            if stripped.startswith("provider:"):
                projects[current_project]["provider"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("environment:"):
                projects[current_project]["environment"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("aliases:"):
                continue
            elif stripped.startswith("- "):
                projects[current_project].setdefault("aliases", []).append(stripped[2:].strip())

    return {"task_type": {"debug_keywords": debug_keywords}, "projects": projects}
