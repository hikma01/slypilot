"""Decision engine for coordinator orchestration."""

from __future__ import annotations

from dataclasses import dataclass

from .execution_guard import ExecutionGuardResult
from .strategy_selector import StrategySelection


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str
    strategy: StrategySelection


def decide(guard: ExecutionGuardResult, strategy: StrategySelection) -> Decision:
    if not guard.allowed:
        return Decision(False, guard.reason, strategy)
    return Decision(True, "approved", strategy)
