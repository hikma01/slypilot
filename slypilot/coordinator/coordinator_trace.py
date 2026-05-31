"""Structured trace emitted by the coordinator."""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class CoordinatorTrace:
    intent: str
    project: str
    strategy: str
    provider: str
    archiops: str
    decision: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ResourceTrace:
    raw_input: str
    detected_paths: list[str]
    normalized_paths: list[str]
    existing_paths: list[str]
    missing_paths: list[str]
    blocked_paths: list[str]
    resource_types: list[str]
    selected_resource: dict[str, object]
    intake_status: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
