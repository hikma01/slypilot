"""Execution guardrails for the coordinator layer."""

from __future__ import annotations

from dataclasses import dataclass

from .coherence_checker import CoherenceResult


@dataclass(frozen=True)
class ExecutionGuardResult:
    allowed: bool
    reason: str


def guard_execution(coherence: CoherenceResult, confidence: str) -> ExecutionGuardResult:
    if not coherence.allowed:
        return ExecutionGuardResult(False, coherence.reason)
    if confidence == "low":
        return ExecutionGuardResult(False, "low_confidence")
    return ExecutionGuardResult(True, "allowed")
