"""Initialize ARCHI OPS minimal structure in the current repository."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from slypilot.cartography_service import generate_cartography


ARCHIOPS_RELATIVE_PATH = Path("Documents/ARCHIOPS")
GLOBAL_INDEX_PATH = Path(__file__).resolve().parents[1] / "archi_ops" / "index.yaml"


@dataclass(frozen=True)
class InitResult:
    project_name: str
    project_root: Path
    archiops_path: Path
    created_files: list[Path]
    updated_index: Path
    warnings: list[str]


def initialize_project(project_root: Path) -> InitResult:
    return initialize_project_with_index(project_root, GLOBAL_INDEX_PATH)


def initialize_project_with_index(project_root: Path, index_path: Path) -> InitResult:
    project_name = project_root.name.lower()
    archiops_path = project_root / ARCHIOPS_RELATIVE_PATH
    archiops_path.mkdir(parents=True, exist_ok=True)
    slypilot_dir = project_root / ".slypilot"
    slypilot_dir.mkdir(parents=True, exist_ok=True)
    memory_path = slypilot_dir / "project_memory.json"
    created_memory = not memory_path.exists()
    if not memory_path.exists():
        _write_file(memory_path, json.dumps({"projects": {}}, ensure_ascii=False, indent=2) + "\n")

    cartography = generate_cartography(project_root, project_name)
    created_files = [
        _write_file(archiops_path / "project.yaml", _render_project_yaml(project_name, project_root)),
        _write_file(archiops_path / "repo-map.md", cartography.repo_map),
        _write_file(archiops_path / "runtime-map.md", cartography.runtime_map),
        _write_file(archiops_path / "dependency-map.md", cartography.dependency_map),
        _write_file(archiops_path / "interpreted-tree.md", cartography.interpreted_tree),
        _write_file(archiops_path / "semantic-index.md", cartography.semantic_index),
        _write_file(archiops_path / "business-map.md", cartography.business_map),
    ]
    if created_memory:
        created_files.append(memory_path)

    warnings = _update_global_index(project_name, project_root, index_path, cartography)

    return InitResult(
        project_name=project_name,
        project_root=project_root,
        archiops_path=archiops_path,
        created_files=created_files,
        updated_index=index_path,
        warnings=warnings,
    )


def _render_project_yaml(project_name: str, project_root: Path) -> str:
    return "\n".join(
        [
            "project:",
            f"  name: {project_name}",
            f"  root: {project_root}",
            "  status: initialized",
            f"  archiops_path: {ARCHIOPS_RELATIVE_PATH}",
            "  created_by: slypilot init",
            "  version: 1",
            "",
        ]
    )


def _write_file(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def _update_global_index(project_name: str, project_root: Path, index_path: Path, cartography: Any) -> list[str]:
    warnings: list[str] = []
    try:
        index_data = json.loads(index_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        warnings.append(f"ARCHI OPS index missing: {index_path}")
        return warnings

    # Identify important files from cartography
    important_files = []
    for entry in cartography.detected_entry_points:
        if entry.endswith("/"):
            continue
        full_path = project_root / entry
        if full_path.is_file():
            important_files.append({
                "path": entry,
                "task_types": ["debug", "patch", "review", "docs", "architecture"],
                "weight": 95 if any(name in entry for name in {"backend.py", "main.py", "app.py", "server.py", "App.jsx", "App.tsx"}) else 90,
                "reason": "detected_entry_point",
                "lines": len(full_path.read_text(encoding="utf-8").splitlines()),
            })

    projects = index_data.setdefault("projects", {})
    projects[project_name] = {
        "root": str(project_root),
        "archiops_path": str(ARCHIOPS_RELATIVE_PATH),
        "status": "initialized",
        "files": important_files,
        "maps": [
            {
                "path": "Documents/ARCHIOPS/project.yaml",
                "task_types": ["architecture", "docs"],
                "weight": 100,
                "reason": "project_registration",
                "lines": 20,
            },
            {
                "path": "Documents/ARCHIOPS/repo-map.md",
                "task_types": ["architecture", "debug", "patch", "review", "docs"],
                "weight": 95,
                "reason": "repo_structure",
                "lines": 60,
            },
            {
                "path": "Documents/ARCHIOPS/runtime-map.md",
                "task_types": ["debug", "patch", "architecture"],
                "weight": 90,
                "reason": "runtime_boundaries",
                "lines": 40,
            },
            {
                "path": "Documents/ARCHIOPS/dependency-map.md",
                "task_types": ["debug", "patch", "architecture"],
                "weight": 85,
                "reason": "dependency_surface",
                "lines": 40,
            },
            {
                "path": "Documents/ARCHIOPS/semantic-index.md",
                "task_types": ["architecture", "debug", "patch", "review", "docs"],
                "weight": 80,
                "reason": "semantic_surface",
                "lines": 40,
            },
            {
                "path": "Documents/ARCHIOPS/interpreted-tree.md",
                "task_types": ["architecture", "debug", "patch", "review", "docs"],
                "weight": 80,
                "reason": "interpreted_tree_surface",
                "lines": 40,
            },
            {
                "path": "Documents/ARCHIOPS/business-map.md",
                "task_types": ["architecture", "debug", "patch", "review", "docs"],
                "weight": 80,
                "reason": "business_logic_surface",
                "lines": 40,
            },
        ],
    }
    index_path.write_text(json.dumps(index_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return warnings
