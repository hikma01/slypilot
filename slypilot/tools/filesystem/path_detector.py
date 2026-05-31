"""Detect bounded local paths in user requests."""

from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path


PATH_PATTERN = re.compile(
    r"(?P<path>(?:~|\.{1,2}|/|[A-Za-z]:\\\\|\\\\)[^\s\"']+)"
)


@dataclass(frozen=True)
class DetectedPath:
    raw_path: str
    normalized_path: str
    source: str = "explicit_user_input"


def detect_paths(raw_input: str, cwd: Path | None = None) -> list[DetectedPath]:
    cwd = cwd or Path.cwd()
    results: list[DetectedPath] = []
    seen: set[str] = set()
    for match in PATH_PATTERN.finditer(raw_input):
        raw_path = match.group("path").rstrip(".,;")
        normalized = _normalize_path(raw_path, cwd)
        if normalized in seen:
            continue
        seen.add(normalized)
        results.append(DetectedPath(raw_path=raw_path, normalized_path=normalized))
    return results


def _normalize_path(raw_path: str, cwd: Path) -> str:
    expanded = raw_path
    if raw_path.startswith("~"):
        expanded = str(Path.home()) + raw_path[1:]
    candidate = Path(expanded)
    if not candidate.is_absolute():
        candidate = (cwd / candidate).resolve(strict=False)
    else:
        candidate = candidate.resolve(strict=False)
    return str(candidate)
