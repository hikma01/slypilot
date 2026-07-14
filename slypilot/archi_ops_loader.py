"""Deterministic ARCHI OPS context selection for SlyPilot V1."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class ContextProfile:
    name: str
    max_files: int
    max_lines: int


@dataclass(frozen=True)
class SelectionItem:
    path: str
    reason: str
    content: str
    lines: int


@dataclass(frozen=True)
class LoaderResult:
    files: list[SelectionItem]
    maps: list[SelectionItem]
    metadata: dict[str, object]
    warnings: list[str]
    knowledge_contract: "KnowledgeContract | None" = None

    @property
    def is_present(self) -> bool:
        return bool(self.files or self.maps)


@dataclass(frozen=True)
class KnowledgeArtifact:
    path: str
    content: str
    reason: str
    exists: bool
    size: int

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "content": self.content,
            "reason": self.reason,
            "exists": self.exists,
            "size": self.size,
        }


@dataclass(frozen=True)
class KnowledgeContract:
    project: str
    repo_map: KnowledgeArtifact | None
    runtime_map: KnowledgeArtifact | None
    dependency_map: KnowledgeArtifact | None
    semantic_index: KnowledgeArtifact | None
    interpreted_tree: KnowledgeArtifact | None
    business_map: KnowledgeArtifact | None
    important_files: list[KnowledgeArtifact]
    selection_reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "project": self.project,
            "repo_map": self.repo_map.to_dict() if self.repo_map else None,
            "runtime_map": self.runtime_map.to_dict() if self.runtime_map else None,
            "dependency_map": self.dependency_map.to_dict() if self.dependency_map else None,
            "semantic_index": self.semantic_index.to_dict() if self.semantic_index else None,
            "interpreted_tree": self.interpreted_tree.to_dict() if self.interpreted_tree else None,
            "business_map": self.business_map.to_dict() if self.business_map else None,
            "important_files": [item.to_dict() for item in self.important_files],
            "selection_reason": self.selection_reason,
        }


PROFILES: dict[str, ContextProfile] = {
    "minimal": ContextProfile("minimal", 5, 1000),
    "standard": ContextProfile("standard", 15, 5000),
    "premium": ContextProfile("premium", 30, 15000),
}


def load_archi_ops_context(
    repository_root: Path,
    project_id: str,
    task_type: str,
    context_profile: str,
    project_root: Path | None = None,
) -> LoaderResult:
    index_path = repository_root / "archi_ops" / "index.yaml"
    warnings: list[str] = []
    if not index_path.exists():
        warnings.append(f"ARCHI OPS index missing: {index_path}")
        return LoaderResult(files=[], maps=[], metadata=_empty_metadata(), warnings=warnings)

    index_data = json.loads(index_path.read_text(encoding="utf-8"))
    profile = PROFILES.get(context_profile, PROFILES["standard"])
    project_data = index_data.get("projects", {}).get(project_id, {})
    if not project_data:
        warnings.append(f"ARCHI OPS project not indexed: {project_id}")
        return LoaderResult(files=[], maps=[], metadata=_empty_metadata(), warnings=warnings)

    matching_files = _matching_items(project_data.get("files", []), task_type)
    matching_maps = _matching_items(project_data.get("maps", []), task_type)
    files = _select_items(matching_files, profile.max_files, profile.max_lines)
    maps = _select_items(matching_maps, profile.max_files, profile.max_lines)
    knowledge_contract = _load_knowledge_contract(project_root or repository_root, project_id, files, maps)

    selected_lines = sum(item.lines for item in files)
    total_tokens_estimated = _estimate_tokens_for_items(files, maps)
    raw_context_tokens_estimated = _estimate_raw_context_tokens(matching_files, matching_maps)

    metadata = {
        "total_tokens_estimated": total_tokens_estimated,
        "estimated_raw_context_tokens": raw_context_tokens_estimated,
        "files_selected": len(files),
        "files_excluded": max(0, len(matching_files) - len(files)),
        "selected_files_count": len(files),
        "selected_lines_count": selected_lines,
        "context_profile": profile.name,
        "max_files": profile.max_files,
        "max_lines": profile.max_lines,
    }

    return LoaderResult(
        files=files,
        maps=maps,
        metadata=metadata,
        warnings=warnings,
        knowledge_contract=knowledge_contract,
    )


def _matching_items(items: list[dict[str, object]], task_type: str) -> list[dict[str, object]]:
    matching = [item for item in items if task_type in item.get("task_types", [])]
    matching.sort(key=lambda item: (-int(item.get("weight", 0)), str(item.get("path", ""))))
    return matching


def _select_items(
    items: list[dict[str, object]],
    max_files: int,
    max_lines: int,
) -> list[SelectionItem]:

    selected: list[SelectionItem] = []
    used_lines = 0
    for item in items:
        if len(selected) >= max_files:
            break
        lines = int(item.get("lines", 0))
        if used_lines + lines > max_lines:
            continue
        path = str(item["path"])
        reason = str(item.get("reason", "task_relevance=selected"))
        content = f"path: {path}\nreason: {reason}\nweight: {item.get('weight', 0)}"
        selected.append(SelectionItem(path=path, reason=reason, content=content, lines=lines))
        used_lines += lines
    return selected


def _estimate_raw_context_tokens(
    matching_files: list[dict[str, object]],
    matching_maps: list[dict[str, object]],
) -> int:
    total_lines = sum(int(item.get("lines", 0)) for item in [*matching_files, *matching_maps])
    return max(1, total_lines * 20)


def _estimate_tokens_for_items(files: list[SelectionItem], maps: list[SelectionItem]) -> int:
    total_chars = sum(len(item.content) for item in [*files, *maps])
    return max(1, total_chars // 4)


def _empty_metadata() -> dict[str, object]:
    return {
        "total_tokens_estimated": 0,
        "files_selected": 0,
        "files_excluded": 0,
        "selected_files_count": 0,
        "selected_lines_count": 0,
        "context_profile": None,
        "max_files": 0,
        "max_lines": 0,
    }


def _load_knowledge_contract(
    project_root: Path,
    project_id: str,
    files: list[SelectionItem],
    maps: list[SelectionItem],
) -> KnowledgeContract:
    def _read(path: str, reason: str) -> KnowledgeArtifact | None:
        full_path = project_root / path
        if not full_path.exists():
            # Fallback to archi_ops/ directory if Documents/ARCHIOPS/ is missing
            alt_path = path.replace("Documents/ARCHIOPS/", "archi_ops/")
            full_path = project_root / alt_path
            if not full_path.exists():
                return None
            path = alt_path
            
        content = full_path.read_text(encoding="utf-8")
        return KnowledgeArtifact(
            path=path,
            content=content,
            reason=reason,
            exists=True,
            size=len(content.encode("utf-8")),
        )

    selected_by_path = {item.path: item.reason for item in [*files, *maps]}
    repo_map = _read("Documents/ARCHIOPS/repo-map.md", selected_by_path.get("Documents/ARCHIOPS/repo-map.md", "selected"))
    runtime_map = _read("Documents/ARCHIOPS/runtime-map.md", selected_by_path.get("Documents/ARCHIOPS/runtime-map.md", "selected"))
    dependency_map = _read(
        "Documents/ARCHIOPS/dependency-map.md",
        selected_by_path.get("Documents/ARCHIOPS/dependency-map.md", "selected"),
    )
    semantic_index = _read(
        "Documents/ARCHIOPS/semantic-index.md",
        selected_by_path.get("Documents/ARCHIOPS/semantic-index.md", "selected"),
    )
    interpreted_tree = _read(
        "Documents/ARCHIOPS/interpreted-tree.md",
        selected_by_path.get("Documents/ARCHIOPS/interpreted-tree.md", "selected"),
    )
    business_map = _read(
        "Documents/ARCHIOPS/business-map.md",
        selected_by_path.get("Documents/ARCHIOPS/business-map.md", "selected"),
    )

    important_files: list[KnowledgeArtifact] = []
    for item in files:
        artifact = _read(item.path, item.reason)
        if artifact is not None:
            important_files.append(artifact)

    selection_reason = ", ".join(
        [item.reason for item in [*files, *maps] if item.reason]
    ) or "deterministic_loader"

    return KnowledgeContract(
        project=project_id,
        repo_map=repo_map,
        runtime_map=runtime_map,
        dependency_map=dependency_map,
        semantic_index=semantic_index,
        interpreted_tree=interpreted_tree,
        business_map=business_map,
        important_files=important_files,
        selection_reason=selection_reason,
    )
