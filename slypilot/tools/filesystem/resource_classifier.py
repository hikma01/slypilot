"""Classify local resources for the filesystem tool."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ResourceClassification:
    resource_type: str
    exists: bool
    detail: str


def classify_resource(path: str | Path) -> ResourceClassification:
    candidate = Path(path).expanduser()
    if not candidate.exists():
        return ResourceClassification("missing_path", False, "path_missing")
    if candidate.is_dir():
        return _classify_directory(candidate)
    return _classify_file(candidate)


def _classify_directory(path: Path) -> ResourceClassification:
    if (path / ".git").exists():
        return ResourceClassification("git_repository", True, "contains_git_directory")
    if (path / "Documents" / "ARCHIOPS" / "project.yaml").exists():
        return ResourceClassification("archiops_project", True, "contains_project_contract")
    if any((path / name).exists() for name in ["package.json", "pyproject.toml", "docker-compose.yml", "README.md"]):
        return ResourceClassification("project_directory", True, "project_surface_detected")
    return ResourceClassification("project_directory", True, "generic_directory")


def _classify_file(path: Path) -> ResourceClassification:
    suffix = path.suffix.lower()
    if suffix in {".md"}:
        return ResourceClassification("markdown_file", True, "markdown")
    if suffix in {".json"}:
        return ResourceClassification("json_file", True, "json")
    if suffix in {".yaml", ".yml"}:
        return ResourceClassification("yaml_file", True, "yaml")
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return ResourceClassification("image_file", True, "image")
    if suffix == ".pdf":
        return ResourceClassification("pdf_file", True, "pdf")
    if suffix in {".txt", ".py", ".js", ".ts", ".mjs", ".html", ".css"}:
        return ResourceClassification("text_file", True, "text")
    return ResourceClassification("unknown_file", True, "unknown")
