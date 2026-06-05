"""Project preparation service for SlyPilot."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from slypilot.archiops_init import initialize_project
from .project_memory import ProjectMemory, ProjectMemoryStore, _contract_snapshot_from_disk


@dataclass(frozen=True)
class ProjectPreparationResult:
    project_name: str
    project_path: str
    preparation_status: str
    created_files: list[str]
    warnings: list[str]
    errors: list[str]


def prepare_project(project_path: str) -> ProjectPreparationResult:
    project_root = Path(project_path)
    project_name = project_root.name.lower() or "unknown"
    contract = project_root / "Documents" / "ARCHIOPS" / "project.yaml"
    memory_path = project_root / ".slypilot" / "project_memory.json"

    if not project_root.exists():
        return ProjectPreparationResult(
            project_name=project_name,
            project_path=project_path,
            preparation_status="failed",
            created_files=[],
            warnings=[],
            errors=["project path does not exist"],
        )

    store = ProjectMemoryStore(project_root)
    current_signature = store.project_signature(project_path)
    index = store.load_index()
    record = index.get("projects", {}).get(store.project_key(project_path), {})
    stored_signature = str(record.get("project_signature", "")) if isinstance(record, dict) else ""

    memory_missing = not memory_path.exists()

    if contract.exists():
        if memory_path.exists():
            if stored_signature and stored_signature == current_signature:
                return ProjectPreparationResult(
                    project_name=project_name,
                    project_path=project_path,
                    preparation_status="already_ready",
                    created_files=[],
                    warnings=[],
                    errors=[],
                )

            loaded_memory = store.load(project_path)
            if loaded_memory is not None:
                store.upsert(loaded_memory, project_signature=current_signature)
                return ProjectPreparationResult(
                    project_name=loaded_memory.project_name,
                    project_path=loaded_memory.project_path,
                    preparation_status="already_ready",
                    created_files=[],
                    warnings=[],
                    errors=[],
                )

        contract_snapshot = _contract_snapshot_from_disk(project_root)
        if contract_snapshot:
            from slypilot.coordinator.expert_interpreter import interpret_expert_diagnostic

            diagnostic = interpret_expert_diagnostic(
                project_name,
                {
                    "knowledge_contract": contract_snapshot,
                    "selected_maps": list(contract_snapshot.keys()),
                    "selected_files": [],
                    "selection_reasons": [],
                },
            )
            memory = ProjectMemory.from_analysis(
                project_name,
                project_path,
                knowledge_contract=contract_snapshot,
                diagnostic=diagnostic,
            )
            store.upsert(memory, project_signature=current_signature)
            return ProjectPreparationResult(
                project_name=memory.project_name,
                project_path=memory.project_path,
                preparation_status="already_ready",
                created_files=[str(memory_path)] if memory_missing else [],
                warnings=[],
                errors=[],
            )

    try:
        result = initialize_project(project_root)
    except Exception as exc:  # pragma: no cover - defensive
        return ProjectPreparationResult(
            project_name=project_name,
            project_path=project_path,
            preparation_status="failed",
            created_files=[],
            warnings=[],
            errors=[str(exc)],
        )

    return ProjectPreparationResult(
        project_name=result.project_name,
        project_path=str(result.project_root),
        preparation_status="success",
        created_files=[str(path) for path in result.created_files],
        warnings=list(result.warnings),
        errors=[],
    )
