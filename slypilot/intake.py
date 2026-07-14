"""Intake normalization for the first detection pass."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Intake:
    raw_request: str
    normalized_request: str
    repository_root: Path


def build_intake(raw_request: str, repository_root: Path) -> Intake:
    normalized_request = " ".join(raw_request.strip().split()).lower()
    return Intake(
        raw_request=raw_request,
        normalized_request=normalized_request,
        repository_root=repository_root,
    )
