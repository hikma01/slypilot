"""Simple JSONL history helpers for SlyPilot V1."""

from __future__ import annotations

import json
from pathlib import Path


def read_history(history_path: Path) -> list[dict[str, object]]:
    if not history_path.exists():
        return []

    entries: list[dict[str, object]] = []
    for line in history_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        entries.append(json.loads(stripped))
    return entries


def latest_history_entry(history_path: Path) -> dict[str, object] | None:
    entries = read_history(history_path)
    return entries[-1] if entries else None
