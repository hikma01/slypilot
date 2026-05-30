from pathlib import Path
import json
import subprocess
import sys


def test_repository_structure():
    root = Path(__file__).resolve().parents[1]

    expected_paths = [
        root / "README.md",
        root / "pyproject.toml",
        root / ".env.example",
        root / ".gitignore",
        root / "slypilot",
        root / "slypilot" / "cli.py",
        root / "slypilot" / "core",
        root / "slypilot" / "adapters",
        root / "slypilot" / "config",
        root / "slypilot" / "prompts",
        root / "slypilot" / "packets",
        root / "slypilot" / "storage",
        root / "slypilot" / "utils",
        root / "archi_ops",
        root / "archi_ops" / "index.md",
        root / "docs",
        root / "docs" / "02A_TASK_PACKET_RULES.md",
        root / "examples",
        root / "examples" / "task_packet_debug.md",
        root / "examples" / "task_packet_patch.md",
        root / "examples" / "task_packet_architecture.md",
        root / "examples" / "invalid",
        root / "examples" / "invalid" / "invalid_missing_metadata.md",
        root / "examples" / "invalid" / "invalid_no_negative_context.md",
        root / "examples" / "invalid" / "invalid_secret_exposed.md",
        root / "examples" / "invalid" / "invalid_token_budget.md",
        root / "schemas",
        root / "schemas" / "task_packet.schema.yaml",
        root / "tests",
    ]

    for path in expected_paths:
        assert path.exists(), f"Missing expected path: {path}"


def test_documentation_inventory():
    root = Path(__file__).resolve().parents[1]
    docs = root / "docs"

    expected_docs = [
        "00_PROJECT_OVERVIEW.md",
        "01_ARCHITECTURE.md",
        "02_TASK_PACKET_STANDARD.md",
        "02A_TASK_PACKET_RULES.md",
        "03_ARCHI_OPS_INDEX.md",
        "04_SECURITY.md",
        "05_PROVIDER_ADAPTERS.md",
        "06_DEVELOPMENT_ROADMAP.md",
        "07_TESTING_STRATEGY.md",
        "08_DECISIONS_LOG.md",
        "09_METRICS_V1.md",
    ]

    for name in expected_docs:
        assert (docs / name).exists(), f"Missing documentation file: {name}"


def test_initial_detection_dry_run():
    root = Path(__file__).resolve().parents[1]
    cases = [
        ("corrige bug upload SlyScan", {"task_type": "debug", "project": "slyscan"}),
        ("analyse architecture SlyPilot", {"task_type": "architecture", "project": "slypilot"}),
        ("explique problème login Hermes", {"task_type": "explain", "project": "hermes"}),
        ("corrige erreur API SlyScan", {"task_type": "debug", "project": "slyscan"}),
    ]

    for request, expected in cases:
        result = subprocess.run(
            [sys.executable, "-m", "slypilot.cli", request, "--dry-run"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(result.stdout)
        assert payload["task_type"] == expected["task_type"]
        assert payload["project"] == expected["project"]
        assert payload["provider"] == "deepseek"
        assert payload["environment"] == "local"
