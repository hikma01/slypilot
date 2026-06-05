"""Persistent project memory for SlyPilot."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from slypilot.coordinator.expert_interpreter import ExpertDiagnostic


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _unique_preserve(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        cleaned = str(value).strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        output.append(cleaned)
    return output


def _as_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        content = value.get("content")
        if content is not None:
            return str(content).strip()
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def _artifact_path(value: object) -> str:
    if isinstance(value, dict):
        return str(value.get("path", "")).strip()
    return str(getattr(value, "path", "") or "").strip()


def _artifact_reason(value: object) -> str:
    if isinstance(value, dict):
        return str(value.get("reason", "")).strip()
    return str(getattr(value, "reason", "") or "").strip()


def _artifact_content(value: object) -> str:
    if isinstance(value, dict):
        return str(value.get("content", "") or "").strip()
    return str(getattr(value, "content", "") or "").strip()


def _section_to_lines(value: object) -> list[str]:
    text = _artifact_content(value)
    return [line.strip() for line in text.splitlines() if line.strip()]


def _find_first(values: list[str]) -> str:
    for value in values:
        cleaned = str(value).strip()
        if cleaned:
            return cleaned
    return ""


def _load_json_text(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass
class ProjectMemory:
    project_name: str
    project_path: str

    technologies: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)

    architecture_summary: str = ""
    business_summary: str = ""
    runtime_summary: str = ""

    risks: list[str] = field(default_factory=list)

    important_files: list[str] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)

    loaded_maps: dict[str, str] = field(default_factory=dict)

    generated_artifacts: list[str] = field(default_factory=list)

    previous_findings: list[str] = field(default_factory=list)

    active_recommendation: str | None = None

    last_analysis_timestamp: str | None = None

    freshness_signature: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ProjectMemory":
        return cls(
            project_name=str(data.get("project_name", "unknown")),
            project_path=str(data.get("project_path", "")),
            technologies=[str(item) for item in data.get("technologies", []) if str(item).strip()],
            domains=[str(item) for item in data.get("domains", []) if str(item).strip()],
            architecture_summary=str(data.get("architecture_summary", "")),
            business_summary=str(data.get("business_summary", "")),
            runtime_summary=str(data.get("runtime_summary", "")),
            risks=[str(item) for item in data.get("risks", []) if str(item).strip()],
            important_files=[str(item) for item in data.get("important_files", []) if str(item).strip()],
            entry_points=[str(item) for item in data.get("entry_points", []) if str(item).strip()],
            loaded_maps={str(key): str(value) for key, value in dict(data.get("loaded_maps", {})).items()},
            generated_artifacts=[str(item) for item in data.get("generated_artifacts", []) if str(item).strip()],
            previous_findings=[str(item) for item in data.get("previous_findings", []) if str(item).strip()],
            active_recommendation=(str(data.get("active_recommendation")) if data.get("active_recommendation") else None),
            last_analysis_timestamp=(str(data.get("last_analysis_timestamp")) if data.get("last_analysis_timestamp") else None),
            freshness_signature=(str(data.get("freshness_signature")) if data.get("freshness_signature") else None),
        )

    @classmethod
    def from_analysis(
        cls,
        project_name: str,
        project_path: str,
        *,
        knowledge_contract: object | None = None,
        diagnostic: ExpertDiagnostic | object | None = None,
        packet: object | None = None,
    ) -> "ProjectMemory":
        contract = _normalize_knowledge_contract(knowledge_contract)
        packet_metadata = getattr(packet, "metadata", {}) if packet is not None else {}
        packet_generated_files = [str(item) for item in getattr(packet, "generated_files", []) if str(item).strip()]
        packet_risks = [str(item) for item in getattr(packet, "risks", []) if str(item).strip()]
        packet_technologies = [str(item) for item in getattr(packet, "technologies", []) if str(item).strip()]
        packet_recommendation = str(getattr(packet, "recommendation", "") or "").strip()

        interpreted = diagnostic if _looks_like_expert_diagnostic(diagnostic) else None
        if interpreted is None and contract:
            from slypilot.coordinator.expert_interpreter import interpret_expert_diagnostic

            interpreted = interpret_expert_diagnostic(
                project_name,
                {
                    "knowledge_contract": contract,
                    "selected_maps": _contract_paths(contract),
                    "selected_files": _important_file_paths(contract),
                },
            )

        detected_technologies = _unique_preserve(
            [
                *packet_technologies,
                *(interpreted.detected_technologies if interpreted else []),
                *_extract_technologies_from_contract(contract),
            ]
        )
        detected_domains = _unique_preserve(
            [
                *(interpreted.detected_domains if interpreted else []),
                *_extract_domains_from_contract(contract),
            ]
        )

        repo_map = contract.get("repo_map")
        runtime_map = contract.get("runtime_map")
        dependency_map = contract.get("dependency_map")
        business_map = contract.get("business_map")
        interpreted_tree = contract.get("interpreted_tree")
        semantic_index = contract.get("semantic_index")
        important_files = _important_file_paths(contract)

        loaded_maps = {
            "repo_map": _artifact_content(repo_map),
            "runtime_map": _artifact_content(runtime_map),
            "dependency_map": _artifact_content(dependency_map),
            "business_map": _artifact_content(business_map),
            "interpreted_tree": _artifact_content(interpreted_tree),
            "semantic_index": _artifact_content(semantic_index),
        }

        architecture_summary = _find_first(
            [
                interpreted.summary[0] if interpreted and interpreted.summary else "",
                packet_metadata.get("architecture_summary", ""),
                _section_to_lines(repo_map)[0] if _section_to_lines(repo_map) else "",
                _section_to_lines(interpreted_tree)[0] if _section_to_lines(interpreted_tree) else "",
            ]
        )
        business_summary = _find_first(
            [
                packet_metadata.get("business_summary", ""),
                interpreted.understood[0] if interpreted and interpreted.understood else "",
                _section_to_lines(business_map)[0] if _section_to_lines(business_map) else "",
            ]
        )
        runtime_summary = _find_first(
            [
                packet_metadata.get("runtime_summary", ""),
                _section_to_lines(runtime_map)[0] if _section_to_lines(runtime_map) else "",
                ", ".join(detected_technologies),
            ]
        )

        risks = _unique_preserve(
            [
                *packet_risks,
                *(interpreted.missing if interpreted else []),
                *(interpreted.why if interpreted else []),
                *_extract_risk_like_lines(interpreted.meaning if interpreted else []),
            ]
        )

        previous_findings = _unique_preserve(
            [
                *(interpreted.summary if interpreted else []),
                *(interpreted.understood if interpreted else []),
                *(interpreted.meaning if interpreted else []),
                *(interpreted.missing if interpreted else []),
                *(interpreted.why if interpreted else []),
                *(interpreted.next_step if interpreted else []),
                packet_recommendation,
                *(packet_metadata.get("selection_reasons", []) if isinstance(packet_metadata.get("selection_reasons", []), list) else []),
            ]
        )
        if not previous_findings and packet_metadata.get("project_memory"):
            previous_findings = _unique_preserve(
                [
                    *(_as_text(item) for item in packet_metadata.get("project_memory", {}).get("previous_findings", [])),
                ]
            )

        generated_artifacts = _unique_preserve(
            [
                *packet_generated_files,
                *(packet_metadata.get("selected_files", []) if isinstance(packet_metadata.get("selected_files", []), list) else []),
                *(packet_metadata.get("selected_maps", []) if isinstance(packet_metadata.get("selected_maps", []), list) else []),
                *important_files,
                *[path for path in _contract_paths(contract) if path],
            ]
        )

        entry_points = _unique_preserve(
            [
                *_derive_entry_points(important_files),
                *_derive_entry_points(packet_generated_files),
                *_derive_entry_points(getattr(interpreted, "detected_files", []) if interpreted else []),
            ]
        )

        active_recommendation = _find_first([packet_recommendation, interpreted.recommendation if interpreted else ""])
        last_analysis_timestamp = _utc_now()
        freshness_signature = _project_signature_from_contract(contract, project_path)

        return cls(
            project_name=project_name,
            project_path=project_path,
            technologies=detected_technologies,
            domains=detected_domains,
            architecture_summary=architecture_summary,
            business_summary=business_summary,
            runtime_summary=runtime_summary,
            risks=risks,
            important_files=important_files,
            entry_points=entry_points,
            loaded_maps=loaded_maps,
            generated_artifacts=generated_artifacts,
            previous_findings=previous_findings,
            active_recommendation=active_recommendation or None,
            last_analysis_timestamp=last_analysis_timestamp,
            freshness_signature=freshness_signature or None,
        )

    def summary_lines(self) -> list[str]:
        lines = [
            f"Projet mémorisé : {self.project_name}",
            f"Chemin : {self.project_path}",
        ]
        if self.technologies:
            lines.append(f"Technologies : {', '.join(self.technologies)}")
        if self.domains:
            lines.append(f"Domaines : {', '.join(self.domains)}")
        if self.architecture_summary:
            lines.append(f"Architecture : {self.architecture_summary}")
        if self.business_summary:
            lines.append(f"Métier : {self.business_summary}")
        if self.runtime_summary:
            lines.append(f"Runtime : {self.runtime_summary}")
        if self.risks:
            lines.append(f"Risques : {', '.join(self.risks[:5])}")
        return lines


class ProjectMemoryStore:
    def __init__(self, repository_root: Path) -> None:
        self.repository_root = repository_root
        self.store_path = repository_root / ".slypilot" / "project_memory.json"
        self.store_path.parent.mkdir(parents=True, exist_ok=True)

    def load_index(self) -> dict[str, object]:
        if not self.store_path.exists():
            return {"projects": {}}
        return _load_json_text(self.store_path)

    def save_index(self, data: dict[str, object]) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def project_key(self, project_path: str) -> str:
        return str(Path(project_path).expanduser().resolve())

    def project_signature(self, project_path: str) -> str:
        project_root = Path(project_path).expanduser()
        pieces: list[str] = []
        for rel_path in _signature_paths():
            path = project_root / rel_path
            if not path.exists():
                pieces.append(f"{rel_path}:missing")
                continue
            stat = path.stat()
            try:
                content = path.read_text(encoding="utf-8")
            except Exception:
                content = ""
            pieces.append(
                f"{rel_path}:{stat.st_mtime_ns}:{stat.st_size}:{sha256(content.encode('utf-8')).hexdigest()}"
            )
        return sha256("|".join(pieces).encode("utf-8")).hexdigest()

    def load(self, project_path: str) -> ProjectMemory | None:
        key = self.project_key(project_path)
        data = self.load_index()
        projects = data.get("projects", {})
        if not isinstance(projects, dict):
            return None
        record = projects.get(key)
        if not isinstance(record, dict):
            return None

        memory_data = record.get("memory")
        if not isinstance(memory_data, dict):
            return None

        memory = ProjectMemory.from_dict(memory_data)
        stored_signature = str(record.get("project_signature", ""))
        current_signature = self.project_signature(project_path)
        if stored_signature and stored_signature != current_signature:
            refreshed = self.refresh_from_disk(memory)
            self.upsert(refreshed, project_signature=current_signature)
            return refreshed

        return memory

    def upsert(self, memory: ProjectMemory, project_signature: str | None = None) -> ProjectMemory:
        data = self.load_index()
        projects = data.setdefault("projects", {})
        if not isinstance(projects, dict):
            projects = {}
            data["projects"] = projects
        key = self.project_key(memory.project_path)
        projects[key] = {
            "project_signature": project_signature or self.project_signature(memory.project_path),
            "updated_at": _utc_now(),
            "memory": memory.to_dict(),
        }
        self.save_index(data)
        return memory

    def upsert_from_analysis(
        self,
        *,
        project_name: str,
        project_path: str,
        knowledge_contract: object | None = None,
        diagnostic: ExpertDiagnostic | object | None = None,
        packet: object | None = None,
    ) -> ProjectMemory:
        memory = ProjectMemory.from_analysis(
            project_name,
            project_path,
            knowledge_contract=knowledge_contract,
            diagnostic=diagnostic,
            packet=packet,
        )
        return self.upsert(memory)

    def refresh_from_disk(self, existing_memory: ProjectMemory) -> ProjectMemory:
        project_root = Path(existing_memory.project_path)
        contract = _contract_snapshot_from_disk(project_root)
        if not contract:
            return existing_memory

        from slypilot.coordinator.expert_interpreter import interpret_expert_diagnostic

        diagnostic = interpret_expert_diagnostic(
            existing_memory.project_name,
            {
                "knowledge_contract": contract,
                "selected_maps": _contract_paths(contract),
                "selected_files": existing_memory.important_files,
                "selection_reasons": existing_memory.previous_findings,
            },
        )
        refreshed = ProjectMemory.from_analysis(
            existing_memory.project_name,
            existing_memory.project_path,
            knowledge_contract=contract,
            diagnostic=diagnostic,
        )
        refreshed.important_files = existing_memory.important_files or refreshed.important_files
        refreshed.generated_artifacts = _unique_preserve([*existing_memory.generated_artifacts, *refreshed.generated_artifacts])
        refreshed.previous_findings = _unique_preserve(
            [
                *existing_memory.previous_findings,
                *refreshed.previous_findings,
                "Mémoire rafraîchie partiellement après modification du projet.",
            ]
        )
        refreshed.active_recommendation = refreshed.active_recommendation or existing_memory.active_recommendation
        refreshed.last_analysis_timestamp = _utc_now()
        refreshed.freshness_signature = self.project_signature(existing_memory.project_path)
        return refreshed


def _normalize_knowledge_contract(knowledge_contract: object | None) -> dict[str, object]:
    if knowledge_contract is None:
        return {}
    if hasattr(knowledge_contract, "to_dict") and callable(getattr(knowledge_contract, "to_dict")):
        return dict(knowledge_contract.to_dict())
    if isinstance(knowledge_contract, dict):
        return dict(knowledge_contract)
    return {}


def _contract_paths(contract: dict[str, object]) -> list[str]:
    paths: list[str] = []
    for key in ("repo_map", "runtime_map", "dependency_map", "business_map", "interpreted_tree", "semantic_index"):
        value = contract.get(key)
        path = _artifact_path(value)
        if path:
            paths.append(path)
    important = contract.get("important_files", [])
    if isinstance(important, list):
        for item in important:
            path = _artifact_path(item)
            if path:
                paths.append(path)
    return _unique_preserve(paths)


def _important_file_paths(contract: dict[str, object]) -> list[str]:
    important = contract.get("important_files", [])
    if not isinstance(important, list):
        return []
    return _unique_preserve([_artifact_path(item) for item in important if _artifact_path(item)])


def _extract_domains_from_contract(contract: dict[str, object]) -> list[str]:
    semantic = contract.get("semantic_index")
    lines = _section_to_lines(semantic)
    domains = [line for line in lines if line.lower() not in {"semantic index", "detected domains"}]
    return domains


def _extract_technologies_from_contract(contract: dict[str, object]) -> list[str]:
    lowered_chunks = " ".join(
        [
            _artifact_content(contract.get("runtime_map")),
            _artifact_content(contract.get("dependency_map")),
            _artifact_content(contract.get("semantic_index")),
            _artifact_content(contract.get("repo_map")),
        ]
    ).lower()
    detected: list[str] = []
    for needle, label in (
        ("python", "Python"),
        ("docker", "Docker"),
        ("postgres", "PostgreSQL"),
        ("sqlite", "SQLite"),
        ("redis", "Redis"),
        ("api", "API"),
        ("worker", "worker"),
        ("service", "service"),
        ("controller", "controller"),
        ("route", "route"),
    ):
        if needle in lowered_chunks and label not in detected:
            detected.append(label)
    return detected


def _extract_risk_like_lines(lines: list[str]) -> list[str]:
    risk_lines: list[str] = []
    for line in lines:
        lowered = line.lower()
        if "risque" in lowered or "limite" in lowered or "warning" in lowered:
            risk_lines.append(line)
    return risk_lines


def _derive_entry_points(paths: list[str]) -> list[str]:
    markers = ("main", "app", "api", "controller", "route", "server", "entry", "handler")
    entries: list[str] = []
    for path in paths:
        lowered = path.lower()
        if any(marker in lowered for marker in markers):
            entries.append(path)
    return _unique_preserve(entries)


def _looks_like_expert_diagnostic(value: object | None) -> bool:
    if value is None:
        return False
    return all(hasattr(value, attr) for attr in ("summary", "understood", "meaning", "missing", "recommendation", "why", "next_step"))


def _project_signature_from_contract(contract: dict[str, object], project_path: str) -> str:
    pieces: list[str] = [project_path.strip()]
    for key in ("repo_map", "runtime_map", "dependency_map", "business_map", "interpreted_tree", "semantic_index"):
        value = contract.get(key)
        pieces.append(_artifact_content(value))
    important = contract.get("important_files", [])
    if isinstance(important, list):
        pieces.extend(_artifact_path(item) for item in important)
    return sha256("|".join(piece for piece in pieces if piece).encode("utf-8")).hexdigest()


def _signature_paths() -> list[str]:
    return [
        "requirements.txt",
        "pyproject.toml",
        "package.json",
        "docker-compose.yml",
        "Documents/ARCHIOPS/project.yaml",
        "Documents/ARCHIOPS/repo-map.md",
        "Documents/ARCHIOPS/runtime-map.md",
        "Documents/ARCHIOPS/dependency-map.md",
        "Documents/ARCHIOPS/business-map.md",
        "Documents/ARCHIOPS/interpreted-tree.md",
        "Documents/ARCHIOPS/semantic-index.md",
    ]


def _contract_snapshot_from_disk(project_root: Path) -> dict[str, object]:
    def _read(path: str, reason: str) -> dict[str, object] | None:
        full_path = project_root / path
        if not full_path.exists():
            alt_path = path.replace("Documents/ARCHIOPS/", "archi_ops/")
            full_path = project_root / alt_path
            if not full_path.exists():
                return None
            path_value = alt_path
        else:
            path_value = path
        content = full_path.read_text(encoding="utf-8")
        return {
            "path": path_value,
            "content": content,
            "reason": reason,
            "exists": True,
            "size": len(content.encode("utf-8")),
        }

    return {
        "repo_map": _read("Documents/ARCHIOPS/repo-map.md", "selected"),
        "runtime_map": _read("Documents/ARCHIOPS/runtime-map.md", "selected"),
        "dependency_map": _read("Documents/ARCHIOPS/dependency-map.md", "selected"),
        "semantic_index": _read("Documents/ARCHIOPS/semantic-index.md", "selected"),
        "interpreted_tree": _read("Documents/ARCHIOPS/interpreted-tree.md", "selected"),
        "business_map": _read("Documents/ARCHIOPS/business-map.md", "selected"),
        "important_files": [],
        "selection_reason": "refresh_from_disk",
    }
