from pathlib import Path


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
        "03_ARCHI_OPS_INDEX.md",
        "04_SECURITY.md",
        "05_PROVIDER_ADAPTERS.md",
        "06_DEVELOPMENT_ROADMAP.md",
        "07_TESTING_STRATEGY.md",
        "08_DECISIONS_LOG.md",
    ]

    for name in expected_docs:
        assert (docs / name).exists(), f"Missing documentation file: {name}"

