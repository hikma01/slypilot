"""Strategy selection for SlyPilot coordinator."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrategySelection:
    name: str
    reason: str


def select_strategy(task_type: str, dry_run: bool = False, live_run: bool = False) -> StrategySelection:
    if task_type == "unknown":
        return StrategySelection("reject", "non_technical_request")
    if live_run:
        return StrategySelection("provider_execution", "live_run_requested")
    if dry_run:
        return StrategySelection("packet_preview", "dry_run_requested")
    return StrategySelection("packet_preview", "default_preview")
