"""Local token estimation helpers for SlyPilot V1."""

from __future__ import annotations


def estimate_tokens(text: str) -> int:
    """Estimate tokens using a simple local heuristic."""
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)
