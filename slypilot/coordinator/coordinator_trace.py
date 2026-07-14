"""Structured trace emitted by the coordinator."""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class AdvisoryTrace:
    advisory: str
    diagnosis: str
    capability_level: str
    recommended_action: str
    alternatives: list[str]
    recommendation_reason: str
    confidence: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CoordinatorTrace:
    intent: str
    project: str
    strategy: str
    provider: str
    archiops: str
    decision: str
    reason: str
    dry_run: bool = False
    live_run: bool = False
    provider_called: bool = False
    intent_trace: dict[str, object] | None = None
    resource_trace: dict[str, object] | None = None
    advisory: AdvisoryTrace | None = None
    skill: str = ""

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
