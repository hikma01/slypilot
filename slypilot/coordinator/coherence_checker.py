"""Coherence validation for the coordinator layer."""

from __future__ import annotations

from dataclasses import dataclass

from slypilot.project_resolver import ResolvedProject


@dataclass(frozen=True)
class CoherenceResult:
    allowed: bool
    reason: str


def check_coherence(project: ResolvedProject) -> CoherenceResult:
    if project.mismatch_detected:
        return CoherenceResult(False, "project_mismatch_detected")
    return CoherenceResult(True, "coherent")
