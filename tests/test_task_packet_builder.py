from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_structured_dry_run_generates_packet():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-m", "slypilot.cli", "corrige bug upload SlyScan", "--dry-run"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    output = result.stdout
    assert "SLYPILOT DRY RUN" in output
    assert "Detection:" in output
    assert "Generated Packet:" in output
    assert "--- TASK PACKET ---" in output

    packet_line = next(
        line for line in output.splitlines() if line.startswith("- slypilot/packets/generated/task_")
    )
    packet_rel_path = packet_line[2:].strip()
    packet_path = root / packet_rel_path
    assert packet_path.exists()

    content = packet_path.read_text(encoding="utf-8")
    assert "# TASK PACKET" in content
    assert "## METADATA" in content
    assert "## SYSTEM_FACTS" in content
    assert "## FORBIDDEN_ASSUMPTIONS" in content
    assert "## OUT_OF_SCOPE" in content
    assert "project: slyscan" in content
    assert "task_type: debug" in content
    assert "## NEGATIVE CONTEXT" in content
    assert "## EXPECTED OUTPUT" in content

    history_path = root / "slypilot" / "storage" / "history.jsonl"
    history_lines = [line for line in history_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert history_lines, "history.jsonl should contain at least one record after dry-run"
    payload = json.loads(history_lines[-1])
    assert payload["project"] == "slyscan"
    assert payload["task_type"] == "debug"
    assert payload["status"] == "packet_generated"


def test_missing_archi_ops_index_warns_instead_of_crashing(tmp_path):
    root = Path(__file__).resolve().parents[1]
    archi_ops_index = root / "archi_ops" / "index.md"
    backup = tmp_path / "index.md"
    backup.write_text(archi_ops_index.read_text(encoding="utf-8"), encoding="utf-8")
    archi_ops_index.unlink()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "slypilot.cli", "analyse architecture SlyPilot", "--dry-run"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "Warnings:" in result.stdout
        assert "ARCHI OPS index missing" in result.stdout
    finally:
        archi_ops_index.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
