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
