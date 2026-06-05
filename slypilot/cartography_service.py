"""Bounded deterministic cartography for ARCHI OPS install."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ALLOWED_TOP_LEVELS = {
    "src",
    "app",
    "apps",
    "docs",
    "tests",
    "routes",
    "services",
    "api",
    "domain",
    "use_cases",
    "business",
    "handlers",
    "workflows",
    "core",
    "workers",
}

ALLOWED_TOP_LEVEL_FILES = {
    "README.md",
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "docker-compose.yml",
    "main.py",
    "app.py",
    "server.py",
}

EXCLUDED_TOP_LEVELS = {
    ".git",
    "node_modules",
    ".venv",
    "dist",
    "build",
    ".cache",
}


@dataclass(frozen=True)
class CartographyResult:
    repo_map: str
    runtime_map: str
    dependency_map: str
    semantic_index: str
    business_map: str
    interpreted_tree: str
    detected_runtimes: list[str]
    detected_dependency_files: list[str]
    detected_domains: list[str]
    detected_entry_points: list[str]
    detected_business_modules: list[str]


def generate_cartography(project_root: Path, project_name: str) -> CartographyResult:
    top_level_entries = _top_level_entries(project_root)
    detected_runtimes = _detect_runtimes(top_level_entries)
    detected_dependency_files = _detect_dependency_files(top_level_entries)
    detected_domains = _detect_domains(top_level_entries)
    
    # Entry Points Detector & Business Map heuristics
    detected_entry_points = _detect_entry_points(top_level_entries)
    detected_business_modules = _detect_business_modules(top_level_entries)

    repo_map = _render_repo_map(project_name, project_root, top_level_entries)
    runtime_map = _render_runtime_map(detected_runtimes, top_level_entries)
    dependency_map = _render_dependency_map(detected_dependency_files)
    semantic_index = _render_semantic_index(detected_domains)
    business_map = _render_business_map(detected_business_modules, detected_entry_points)
    interpreted_tree = _render_interpreted_tree(project_name, top_level_entries, detected_entry_points, detected_business_modules)

    return CartographyResult(
        repo_map=repo_map,
        runtime_map=runtime_map,
        dependency_map=dependency_map,
        semantic_index=semantic_index,
        business_map=business_map,
        interpreted_tree=interpreted_tree,
        detected_runtimes=detected_runtimes,
        detected_dependency_files=detected_dependency_files,
        detected_domains=detected_domains,
        detected_entry_points=detected_entry_points,
        detected_business_modules=detected_business_modules,
    )


def _top_level_entries(project_root: Path) -> list[str]:
    entries: list[str] = []
    for child in sorted(project_root.iterdir(), key=lambda path: path.name.lower()):
        if child.name in EXCLUDED_TOP_LEVELS:
            continue
        if child.is_dir() and child.name in ALLOWED_TOP_LEVELS:
            entries.append(f"{child.name}/")
            continue
        if child.is_file() and child.name in ALLOWED_TOP_LEVEL_FILES:
            entries.append(child.name)
    return entries


def _detect_runtimes(entries: list[str]) -> list[str]:
    runtimes: list[str] = []
    if "package.json" in entries or any(entry.startswith("src/") or entry.startswith("app/") for entry in entries):
        runtimes.append("node")
    if "pyproject.toml" in entries or "requirements.txt" in entries:
        runtimes.append("python")
    if "docker-compose.yml" in entries:
        runtimes.append("docker")
    return runtimes


def _detect_dependency_files(entries: list[str]) -> list[str]:
    return [name for name in ("package.json", "requirements.txt", "pyproject.toml", "docker-compose.yml") if name in entries]


def _detect_domains(entries: list[str]) -> list[str]:
    domains: list[str] = []
    if any(entry.startswith(("src/", "app/", "apps/", "routes/", "services/", "api/")) for entry in entries):
        domains.extend(["api", "frontend"])
    if "docs/" in entries:
        domains.append("docs")
    if "tests/" in entries:
        domains.append("tests")
    if "package.json" in entries or "pyproject.toml" in entries or "requirements.txt" in entries:
        domains.append("config")
    return _dedupe(domains)


def _detect_entry_points(entries: list[str]) -> list[str]:
    points: list[str] = []
    for entry in entries:
        if entry in {"main.py", "app.py", "server.py"}:
            points.append(entry)
        if entry in {"routes/", "api/", "workers/"}:
            points.append(entry)
    return points


def _detect_business_modules(entries: list[str]) -> list[str]:
    modules: list[str] = []
    patterns = {"services/", "domain/", "use_cases/", "business/", "handlers/", "workflows/", "core/", "app/", "src/"}
    for entry in entries:
        if entry in patterns:
            modules.append(entry)
    return modules


def _render_repo_map(project_name: str, project_root: Path, top_level_entries: list[str]) -> str:
    excluded = sorted(EXCLUDED_TOP_LEVELS)
    return "\n".join(
        [
            "# REPO MAP",
            "",
            "## PROJECT",
            "",
            project_name,
            "",
            "## ROOT",
            "",
            str(project_root),
            "",
            "## TOP LEVEL STRUCTURE",
            "",
            *_bullet_lines(top_level_entries),
            "",
            "## EXCLUDED",
            "",
            *[f"- {entry}" for entry in excluded],
        ]
    )


def _render_runtime_map(detected_runtimes: list[str], top_level_entries: list[str]) -> str:
    entrypoints = [entry for entry in top_level_entries if entry in {"package.json", "docker-compose.yml"} or entry.endswith("/")]
    return "\n".join(
        [
            "# RUNTIME MAP",
            "",
            "## DETECTED RUNTIMES",
            "",
            *_bullet_lines(detected_runtimes),
            "",
            "## ENTRYPOINT CANDIDATES",
            "",
            *_bullet_lines(entrypoints),
        ]
    )


def _render_dependency_map(detected_dependency_files: list[str]) -> str:
    return "\n".join(
        [
            "# DEPENDENCY MAP",
            "",
            "## DETECTED FILES",
            "",
            *_bullet_lines(detected_dependency_files),
            "",
            "## NOTES",
            "",
            "Generated by deterministic scan.",
            "No dependency installation executed.",
        ]
    )


def _render_semantic_index(detected_domains: list[str]) -> str:
    return "\n".join(
        [
            "# SEMANTIC INDEX",
            "",
            "## PURPOSE",
            "",
            "Initial ARCHI OPS semantic index.",
            "",
            "## DETECTED DOMAINS",
            "",
            *_bullet_lines(detected_domains),
            "",
            "## LIMITS",
            "",
            "This file is generated from a bounded scan.",
            "It must be improved manually after real incidents.",
        ]
    )


def _render_business_map(business_modules: list[str], entry_points: list[str]) -> str:
    return "\n".join(
        [
            "# BUSINESS MAP",
            "",
            "## PURPOSE",
            "",
            "Identify the core business logic and functional value of the project.",
            "",
            "## PRIMARY BUSINESS MODULES",
            "",
            *_bullet_lines(business_modules),
            "",
            "## ENTRY POINTS",
            "",
            *_bullet_lines(entry_points),
            "",
            "## RISK ZONES",
            "",
            "- Pending deeper exploration to identify critical business workflows.",
            "",
            "## SUMMARY",
            "",
            "Generated by deterministic scan based on heuristics.",
            "Must be manually refined by the architect.",
        ]
    )


def _render_interpreted_tree(
    project_name: str,
    top_level_entries: list[str],
    detected_entry_points: list[str],
    detected_business_modules: list[str],
) -> str:
    lines = [
        "# INTERPRETED TREE",
        "",
        "## PROJECT",
        "",
        project_name,
        "",
        "## STRUCTURE",
        "",
        *_bullet_lines(top_level_entries),
        "",
        "## ENTRY POINTS",
        "",
        *_bullet_lines(detected_entry_points),
        "",
        "## BUSINESS MODULES",
        "",
        *_bullet_lines(detected_business_modules),
        "",
        "## SUMMARY",
        "",
        "Bounded structural tree generated by the centralized ArchiOps bootstrap.",
    ]
    return "\n".join(lines)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _bullet_lines(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["- none"]
