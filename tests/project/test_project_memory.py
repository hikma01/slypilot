from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase

from slypilot.project import ProjectMemory, ProjectMemoryStore


def _write_archiops_files(project_root: Path, runtime_map: str) -> None:
    archiops_dir = project_root / "Documents" / "ARCHIOPS"
    archiops_dir.mkdir(parents=True, exist_ok=True)
    (archiops_dir / "repo-map.md").write_text("# REPO MAP\n- docker-compose.yml\n- requirements.txt\n", encoding="utf-8")
    (archiops_dir / "runtime-map.md").write_text(runtime_map, encoding="utf-8")
    (archiops_dir / "dependency-map.md").write_text("# DEPENDENCY MAP\n- requirements.txt\n- docker-compose.yml\n", encoding="utf-8")
    (archiops_dir / "business-map.md").write_text("# BUSINESS MAP\n- api\n- service\n", encoding="utf-8")
    (archiops_dir / "interpreted-tree.md").write_text("# INTERPRETED TREE\n- /core/\n- /api/v1/\n", encoding="utf-8")
    (archiops_dir / "semantic-index.md").write_text("# SEMANTIC INDEX\n- api\n- config\n- tests\n", encoding="utf-8")


def _knowledge_contract(runtime_map: str) -> dict[str, object]:
    return {
        "repo_map": {
            "path": "Documents/ARCHIOPS/repo-map.md",
            "reason": "repo_structure",
            "content": "# REPO MAP\n- docker-compose.yml\n- requirements.txt",
            "exists": True,
            "size": 52,
        },
        "runtime_map": {
            "path": "Documents/ARCHIOPS/runtime-map.md",
            "reason": "runtime_detection",
            "content": runtime_map,
            "exists": True,
            "size": len(runtime_map.encode("utf-8")),
        },
        "dependency_map": {
            "path": "Documents/ARCHIOPS/dependency-map.md",
            "reason": "dependency_surface",
            "content": "# DEPENDENCY MAP\n- requirements.txt\n- docker-compose.yml",
            "exists": True,
            "size": 58,
        },
        "business_map": {
            "path": "Documents/ARCHIOPS/business-map.md",
            "reason": "business_surface",
            "content": "# BUSINESS MAP\n- api\n- service",
            "exists": True,
            "size": 31,
        },
        "interpreted_tree": {
            "path": "Documents/ARCHIOPS/interpreted-tree.md",
            "reason": "tree_surface",
            "content": "# INTERPRETED TREE\n- /core/\n- /api/v1/",
            "exists": True,
            "size": 39,
        },
        "semantic_index": {
            "path": "Documents/ARCHIOPS/semantic-index.md",
            "reason": "semantic_surface",
            "content": "# SEMANTIC INDEX\n- api\n- config\n- tests",
            "exists": True,
            "size": 39,
        },
        "important_files": [
            {
                "path": "docker-compose.yml",
                "reason": "configuration runtime",
                "content": "version: '3.9'",
                "exists": True,
                "size": 14,
            },
            {
                "path": "requirements.txt",
                "reason": "dépendances Python",
                "content": "fastapi\nuvicorn",
                "exists": True,
                "size": 15,
            },
        ],
        "selection_reason": "selected",
    }


class ProjectMemoryTests(TestCase):
    def test_memory_persists_rich_signals(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir) / "SlyAudit"
            project_root.mkdir()
            runtime_map = "# RUNTIME MAP\n- Python\n- Docker"
            _write_archiops_files(project_root, runtime_map)
            store = ProjectMemoryStore(project_root)

            packet = SimpleNamespace(
                generated_files=["slypilot/packets/generated/task_123.md"],
                metadata={
                    "selected_maps": [
                        "Documents/ARCHIOPS/repo-map.md",
                        "Documents/ARCHIOPS/runtime-map.md",
                        "Documents/ARCHIOPS/dependency-map.md",
                    ],
                    "selected_files": ["docker-compose.yml", "requirements.txt"],
                    "selection_reasons": [
                        "docker-compose.yml: runtime_configuration",
                        "requirements.txt: python_dependencies",
                    ],
                    "knowledge_contract": _knowledge_contract(runtime_map),
                },
                risks=["cartographie encore initiale"],
                technologies=["Python", "Docker"],
                recommendation="Explorer l'arborescence métier.",
            )

            memory = ProjectMemory.from_analysis(
                "SlyAudit",
                str(project_root),
                knowledge_contract=_knowledge_contract(runtime_map),
                packet=packet,
            )
            self.assertIn("Python", memory.technologies)
            self.assertIn("runtime_map", memory.loaded_maps)
            self.assertTrue(memory.risks)
            self.assertTrue(memory.previous_findings)
            self.assertTrue(memory.freshness_signature)

            signature = store.project_signature(str(project_root))
            store.upsert(memory, project_signature=signature)
            loaded = store.load(str(project_root))

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.project_name, "SlyAudit")
        self.assertIn("Docker", loaded.technologies)
        self.assertIn("docker-compose.yml", loaded.important_files)
        self.assertIn("runtime_map", loaded.loaded_maps)
        self.assertTrue(loaded.previous_findings)
        self.assertTrue(loaded.freshness_signature)

    def test_memory_refreshes_when_project_changes(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir) / "SlyAudit"
            project_root.mkdir()
            runtime_map_v1 = "# RUNTIME MAP\n- Python\n- Docker"
            _write_archiops_files(project_root, runtime_map_v1)
            store = ProjectMemoryStore(project_root)

            memory = ProjectMemory.from_analysis(
                "SlyAudit",
                str(project_root),
                knowledge_contract=_knowledge_contract(runtime_map_v1),
            )
            store.upsert(memory, project_signature=store.project_signature(str(project_root)))

            runtime_map_v2 = "# RUNTIME MAP\n- Python\n- Docker\n- FastAPI"
            (project_root / "Documents" / "ARCHIOPS" / "runtime-map.md").write_text(runtime_map_v2, encoding="utf-8")

            refreshed = store.load(str(project_root))

        self.assertIsNotNone(refreshed)
        self.assertIn("FastAPI", refreshed.loaded_maps["runtime_map"])
        self.assertIn("Mémoire rafraîchie partiellement", " ".join(refreshed.previous_findings))
        self.assertTrue(refreshed.freshness_signature)
