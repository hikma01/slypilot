"""Intent analysis for the coordinator layer."""

from __future__ import annotations

from dataclasses import dataclass

from slypilot.classifier import Classification, classify_intake
from slypilot.intake import Intake
from slypilot.resource_resolver import ResourceIntakeResult


ANALYSIS_ACTION_TERMS = [
    "analyse",
    "analyser",
    "vérifie",
    "vérifier",
    "verifie",
    "verifier",
    "check",
    "inspecte",
    "inspecter",
    "audit",
    "audite",
    "auditer",
    "diagnostique",
    "diagnostiquer",
    "regarde",
    "explore",
    "explorer",
]


@dataclass(frozen=True)
class IntentAnalysis:
    task_type: str
    confidence: str
    classification: Classification


@dataclass(frozen=True)
class IntentFusionResult:
    raw_input: str
    normalized_input: str
    detected_action_terms: list[str]
    detected_intent: str
    intent_confidence: float
    detected_paths: list[str]
    resource_type: str
    project_name: str
    fusion_result: str
    final_decision: str
    ambiguity_reason: str | None

    @property
    def task_type(self) -> str:
        return self.detected_intent

    def to_dict(self) -> dict[str, object]:
        return {
            "raw_input": self.raw_input,
            "normalized_input": self.normalized_input,
            "detected_action_terms": self.detected_action_terms,
            "detected_intent": self.detected_intent,
            "intent_confidence": self.intent_confidence,
            "detected_paths": self.detected_paths,
            "resource_type": self.resource_type,
            "project_name": self.project_name,
            "fusion_result": self.fusion_result,
            "final_decision": self.final_decision,
            "ambiguity_reason": self.ambiguity_reason,
        }


def analyze_intent(intake: Intake, repository_root) -> IntentAnalysis:
    classification = classify_intake(intake, repository_root)
    confidence = "high" if classification.task_type != "unknown" else "low"
    return IntentAnalysis(
        task_type=classification.task_type,
        confidence=confidence,
        classification=classification,
    )


def resolve_intent_with_resource(intake: Intake, resource: ResourceIntakeResult) -> IntentFusionResult:
    normalized_input = intake.normalized_request.lower()
    detected_action_terms = [term for term in ANALYSIS_ACTION_TERMS if term in normalized_input]
    detected_intent = "analyze_project" if detected_action_terms else "unknown"
    intent_confidence = 0.95 if detected_action_terms else 0.2
    resource_type = str(resource.resource_types[0]) if resource.resource_types else ""
    project_name = resource.project_name or "unknown"

    if resource.intake_status == "blocked":
        return IntentFusionResult(
            raw_input=intake.raw_request,
            normalized_input=normalized_input,
            detected_action_terms=detected_action_terms,
            detected_intent=detected_intent,
            intent_confidence=intent_confidence,
            detected_paths=list(resource.detected_paths),
            resource_type=resource_type,
            project_name=project_name,
            fusion_result="blocked_sensitive_path",
            final_decision="block_sensitive_path",
            ambiguity_reason="sensitive path blocked",
        )

    if resource.intake_status == "missing_path":
        return IntentFusionResult(
            raw_input=intake.raw_request,
            normalized_input=normalized_input,
            detected_action_terms=detected_action_terms,
            detected_intent=detected_intent,
            intent_confidence=intent_confidence,
            detected_paths=list(resource.detected_paths),
            resource_type=resource_type,
            project_name=project_name,
            fusion_result="missing_path",
            final_decision="block_missing_path",
            ambiguity_reason="local path does not exist",
        )

    if detected_action_terms and resource_type in {"project_directory", "git_repository", "archiops_project"}:
        return IntentFusionResult(
            raw_input=intake.raw_request,
            normalized_input=normalized_input,
            detected_action_terms=detected_action_terms,
            detected_intent="analyze_project",
            intent_confidence=0.95,
            detected_paths=list(resource.detected_paths),
            resource_type=resource_type,
            project_name=project_name,
            fusion_result="analysis_request_with_project_path",
            final_decision="auto_prepare_then_analyze",
            ambiguity_reason=None,
        )

    if not detected_action_terms and resource_type in {"project_directory", "git_repository", "archiops_project"}:
        return IntentFusionResult(
            raw_input=intake.raw_request,
            normalized_input=normalized_input,
            detected_action_terms=detected_action_terms,
            detected_intent="unknown",
            intent_confidence=0.2,
            detected_paths=list(resource.detected_paths),
            resource_type=resource_type,
            project_name=project_name,
            fusion_result="project_path_needs_choice",
            final_decision="ask_project_action_choice",
            ambiguity_reason="project path without action verb",
        )

    if not resource.detected_paths:
        return IntentFusionResult(
            raw_input=intake.raw_request,
            normalized_input=normalized_input,
            detected_action_terms=detected_action_terms,
            detected_intent=detected_intent,
            intent_confidence=intent_confidence,
            detected_paths=[],
            resource_type=resource_type,
            project_name=project_name,
            fusion_result="no_resource",
            final_decision="no_resource",
            ambiguity_reason=None,
        )

    return IntentFusionResult(
        raw_input=intake.raw_request,
        normalized_input=normalized_input,
        detected_action_terms=detected_action_terms,
        detected_intent=detected_intent,
        intent_confidence=intent_confidence,
        detected_paths=list(resource.detected_paths),
        resource_type=resource_type,
        project_name=project_name,
        fusion_result="ambiguous",
        final_decision="ask_project_action_choice",
        ambiguity_reason="unable to bind intent to resource",
    )
