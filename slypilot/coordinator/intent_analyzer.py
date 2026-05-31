"""Intent analysis for the coordinator layer."""

from __future__ import annotations

from dataclasses import dataclass

from slypilot.classifier import Classification, classify_intake
from slypilot.intake import Intake


@dataclass(frozen=True)
class IntentAnalysis:
    task_type: str
    confidence: str
    classification: Classification


def analyze_intent(intake: Intake, repository_root) -> IntentAnalysis:
    classification = classify_intake(intake, repository_root)
    confidence = "high" if classification.task_type != "unknown" else "low"
    return IntentAnalysis(
        task_type=classification.task_type,
        confidence=confidence,
        classification=classification,
    )
