from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import TestCase

from slypilot.coordinator import coordinate_request
from slypilot.intake import build_intake
from slypilot.archiops_init import initialize_project
from slypilot.project import ProjectMemoryStore


class ArchiOpsDeploymentModelTests(TestCase):
    def test_bootstrap_creates_local_artifacts_and_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir) / "DemoProject"
            project_root.mkdir()
            (project_root / "README.md").write_text("# Demo\n", encoding="utf-8")
            (project_root / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
            (project_root / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
            (project_root / "src").mkdir()

            result = initialize_project(project_root)

            expected_paths = {
                project_root / "Documents" / "ARCHIOPS" / "project.yaml",
                project_root / "Documents" / "ARCHIOPS" / "repo-map.md",
                project_root / "Documents" / "ARCHIOPS" / "runtime-map.md",
                project_root / "Documents" / "ARCHIOPS" / "dependency-map.md",
                project_root / "Documents" / "ARCHIOPS" / "interpreted-tree.md",
                project_root / "Documents" / "ARCHIOPS" / "semantic-index.md",
                project_root / "Documents" / "ARCHIOPS" / "business-map.md",
                project_root / ".slypilot" / "project_memory.json",
            }

            self.assertTrue(expected_paths.issubset(set(result.created_files)))
            for path in expected_paths:
                self.assertTrue(path.exists(), f"missing bootstrap artifact: {path}")

            archiops_names = sorted(child.name for child in (project_root / "Documents" / "ARCHIOPS").iterdir())
            self.assertEqual(
                archiops_names,
                sorted(
                    [
                        "business-map.md",
                        "dependency-map.md",
                        "interpreted-tree.md",
                        "project.yaml",
                        "repo-map.md",
                        "runtime-map.md",
                        "semantic-index.md",
                    ]
                ),
            )

            memory_payload = json.loads((project_root / ".slypilot" / "project_memory.json").read_text(encoding="utf-8"))
            self.assertEqual(memory_payload, {"projects": {}})

    def test_signature_refreshes_on_dependency_file_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir) / "DemoProject"
            project_root.mkdir()
            (project_root / "README.md").write_text("# Demo\n", encoding="utf-8")
            (project_root / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
            (project_root / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
            (project_root / "Documents" / "ARCHIOPS").mkdir(parents=True, exist_ok=True)
            (project_root / "Documents" / "ARCHIOPS" / "project.yaml").write_text(
                "project:\n  name: demoproject\n  root: /tmp/demo\n  status: initialized\n",
                encoding="utf-8",
            )

            store = ProjectMemoryStore(project_root)
            first_signature = store.project_signature(str(project_root))
            (project_root / "requirements.txt").write_text("fastapi\nuvicorn\n", encoding="utf-8")
            second_signature = store.project_signature(str(project_root))

            self.assertNotEqual(first_signature, second_signature)

    def test_analysis_bootstraps_missing_archiops_locally(self) -> None:
        with tempfile.TemporaryDirectory(dir="/Users/hakimradi/Nextcloud/SlyProjet") as tmp_dir:
            repo_root = Path("/Users/hakimradi/Nextcloud/SlyProjet/SlyPilot")
            project_root = Path(tmp_dir) / "BootstrapDemo"
            project_root.mkdir()
            (project_root / "README.md").write_text("# Demo\n", encoding="utf-8")
            (project_root / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
            (project_root / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
            (project_root / "src").mkdir()

            intake = build_intake(f"analyse {project_root}", repo_root)
            result = coordinate_request(intake, repo_root, current_working_directory=project_root, dry_run=True)

            self.assertEqual(result.project.name, "bootstrapdemo")
            self.assertTrue((project_root / "Documents" / "ARCHIOPS" / "project.yaml").exists())
            self.assertTrue((project_root / "Documents" / "ARCHIOPS" / "interpreted-tree.md").exists())
            self.assertTrue((project_root / ".slypilot" / "project_memory.json").exists())
            self.assertTrue(result.packet is not None or result.decision.allowed)
            self.assertFalse((project_root / "slypilot").exists())
