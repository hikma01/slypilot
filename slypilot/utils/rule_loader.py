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
    project_order: list[str] = []
    current_project: str | None = None
    in_projects_block = False
    in_aliases_block = False

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("default_project:"):
            default_project = stripped.split(":", 1)[1].strip()
            continue
        if stripped == "projects:":
            in_projects_block = True
            current_project = None
            in_aliases_block = False
            continue
        if not in_projects_block:
            continue
        if line.startswith("  ") and not line.startswith("    "):
            if stripped.endswith(":") and stripped != "aliases:":
                current_project = stripped[:-1]
                if current_project not in projects:
                    project_order.append(current_project)
                projects.setdefault(current_project, {"aliases": []})
                in_aliases_block = False
            continue
        if current_project is None:
            continue
        if stripped == "aliases:":
            in_aliases_block = True
            projects[current_project].setdefault("aliases", [])
            continue
        if stripped.startswith("provider:"):
            projects[current_project]["provider"] = stripped.split(":", 1)[1].strip()
            continue
        if stripped.startswith("environment:"):
            projects[current_project]["environment"] = stripped.split(":", 1)[1].strip()
            continue
        if in_aliases_block and stripped.startswith("- "):
            projects[current_project]["aliases"].append(stripped[2:].strip())

    return {"default_project": default_project, "projects": projects, "project_order": project_order}


def _parse_classifier_rules(lines: list[str]) -> dict[str, object]:
    ordered_rules: list[dict[str, object]] = []
    current_section: str | None = None
    current_project: str | None = None
    projects: dict[str, dict[str, object]] = {}
    current_rule: dict[str, object] | None = None
    in_keywords_block = False
    in_projects_block = False
    in_aliases_block = False

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "task_type:":
            current_section = "task_type"
            current_rule = None
            in_keywords_block = False
            continue
        if stripped == "projects:":
            current_section = "projects"
            in_projects_block = True
            current_project = None
            in_aliases_block = False
            continue
        if current_section == "task_type" and stripped == "ordered_rules:":
            continue
        if current_section == "task_type" and stripped.startswith("- task_type:"):
            current_rule = {"task_type": stripped.split(":", 1)[1].strip(), "keywords": []}
            ordered_rules.append(current_rule)
            in_keywords_block = False
            continue
        if current_section == "task_type" and stripped == "keywords:" and current_rule is not None:
            in_keywords_block = True
            continue
        if current_section == "task_type" and in_keywords_block and stripped.startswith("- "):
            current_rule["keywords"].append(stripped[2:].strip())
            continue
        if current_section == "projects" and line.startswith("  ") and not line.startswith("    ") and stripped.endswith(":") and stripped != "aliases:":
            current_project = stripped[:-1]
            projects.setdefault(current_project, {"aliases": []})
            in_aliases_block = False
            continue
        if current_section == "projects" and stripped == "aliases:" and current_project is not None:
            in_aliases_block = True
            continue
        if current_section == "projects" and current_project is not None and stripped.startswith("provider:"):
            projects[current_project]["provider"] = stripped.split(":", 1)[1].strip()
            continue
        if current_section == "projects" and current_project is not None and stripped.startswith("environment:"):
            projects[current_project]["environment"] = stripped.split(":", 1)[1].strip()
            continue
        if current_section == "projects" and current_project is not None and in_aliases_block and stripped.startswith("- "):
            projects[current_project].setdefault("aliases", []).append(stripped[2:].strip())

    return {"task_type": {"ordered_rules": ordered_rules}, "projects": projects, "project_order": list(projects)}
