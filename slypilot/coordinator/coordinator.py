"""Central coordinator for SlyPilot V2."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from slypilot.archi_ops_loader import load_archi_ops_context
from slypilot.intake import Intake
from slypilot.resource_resolver import resolve_resources
from slypilot.project_resolver import ResolvedProject, resolve_project
from slypilot.task_packet_builder import BuiltPacket, build_task_packet

from .coherence_checker import CoherenceResult, check_coherence
from .decision_engine import Decision, decide
from .execution_guard import ExecutionGuardResult, guard_execution
from .intent_analyzer import IntentAnalysis, analyze_intent
from .coordinator_trace import CoordinatorTrace, ResourceTrace
from .prompt_loader import load_coordinator_prompt
from .strategy_selector import StrategySelection, select_strategy


@dataclass(frozen=True)
class CoordinatorResult:
    intake: Intake
    system_prompt: str
    resource: ResourceTrace
    intent: IntentAnalysis
    project: ResolvedProject
    coherence: CoherenceResult
    guard: ExecutionGuardResult
    strategy: StrategySelection
    decision: Decision
    trace: CoordinatorTrace
    packet: BuiltPacket | None
    block_reason: str | None = None


def coordinate_request(
    intake: Intake,
    repository_root: Path,
    current_working_directory: Path | None = None,
    dry_run: bool = False,
    live_run: bool = False,
) -> CoordinatorResult:
    system_prompt = load_coordinator_prompt(repository_root / "prompts" / "coordinator")
    resource_result = resolve_resources(intake.raw_request, current_working_directory or Path.cwd())
    if resource_result.blocked_paths:
        trace = CoordinatorTrace(
            intent="blocked",
            project="unknown",
            strategy="reject",
            provider="none",
            archiops="enabled",
            decision="blocked",
            reason="sensitive path blocked",
        )
        resource_trace = ResourceTrace(
            raw_input=resource_result.raw_input,
            detected_paths=resource_result.detected_paths,
            normalized_paths=resource_result.normalized_paths,
            existing_paths=resource_result.existing_paths,
            missing_paths=resource_result.missing_paths,
            blocked_paths=resource_result.blocked_paths,
            resource_types=resource_result.resource_types,
            selected_resource=resource_result.resource_trace["selected_resource"],
            intake_status=resource_result.intake_status,
        )
        return CoordinatorResult(
            intake=intake,
            system_prompt=system_prompt,
            resource=resource_trace,
            intent=IntentAnalysis(task_type="unknown", confidence="low", classification=analyze_intent(intake, repository_root).classification),
            project=ResolvedProject(name="unknown", provider="none", environment="local", requested_project="unknown", resolution_source="blocked_path", confidence="low", fallback_used=False, mismatch_detected=True),
            coherence=CoherenceResult(False, "sensitive_path"),
            guard=ExecutionGuardResult(False, "sensitive_path"),
            strategy=StrategySelection("reject", "sensitive_path"),
            decision=Decision(False, "sensitive_path", StrategySelection("reject", "sensitive_path")),
            trace=trace,
            packet=None,
            block_reason="sensitive path blocked",
        )
    if len(resource_result.detected_paths) > 1:
        trace = CoordinatorTrace(
            intent="ambiguous",
            project="unknown",
            strategy="ask_clarification",
            provider="none",
            archiops="enabled",
            decision="ask_clarification",
            reason="multiple local paths detected",
        )
        resource_trace = ResourceTrace(
            raw_input=resource_result.raw_input,
            detected_paths=resource_result.detected_paths,
            normalized_paths=resource_result.normalized_paths,
            existing_paths=resource_result.existing_paths,
            missing_paths=resource_result.missing_paths,
            blocked_paths=resource_result.blocked_paths,
            resource_types=resource_result.resource_types,
            selected_resource=resource_result.resource_trace["selected_resource"],
            intake_status="ambiguous",
        )
        return CoordinatorResult(
            intake=intake,
            system_prompt=system_prompt,
            resource=resource_trace,
            intent=IntentAnalysis(task_type="unknown", confidence="low", classification=analyze_intent(intake, repository_root).classification),
            project=ResolvedProject(name="unknown", provider="none", environment="local", requested_project="unknown", resolution_source="ambiguous_paths", confidence="low", fallback_used=False, mismatch_detected=True),
            coherence=CoherenceResult(False, "multiple local paths detected"),
            guard=ExecutionGuardResult(False, "multiple local paths detected"),
            strategy=StrategySelection("ask_clarification", "multiple local paths detected"),
            decision=Decision(False, "multiple local paths detected", StrategySelection("ask_clarification", "multiple local paths detected")),
            trace=trace,
            packet=None,
            block_reason="multiple local paths detected",
        )
    if resource_result.missing_paths and not resource_result.existing_paths:
        trace = CoordinatorTrace(
            intent="blocked",
            project="unknown",
            strategy="reject",
            provider="none",
            archiops="enabled",
            decision="blocked",
            reason="local path does not exist",
        )
        resource_trace = ResourceTrace(
            raw_input=resource_result.raw_input,
            detected_paths=resource_result.detected_paths,
            normalized_paths=resource_result.normalized_paths,
            existing_paths=resource_result.existing_paths,
            missing_paths=resource_result.missing_paths,
            blocked_paths=resource_result.blocked_paths,
            resource_types=resource_result.resource_types,
            selected_resource=resource_result.resource_trace["selected_resource"],
            intake_status=resource_result.intake_status,
        )
        return CoordinatorResult(
            intake=intake,
            system_prompt=system_prompt,
            resource=resource_trace,
            intent=IntentAnalysis(task_type="unknown", confidence="low", classification=analyze_intent(intake, repository_root).classification),
            project=ResolvedProject(name="unknown", provider="none", environment="local", requested_project="unknown", resolution_source="missing_path", confidence="low", fallback_used=False, mismatch_detected=True),
            coherence=CoherenceResult(False, "local path does not exist"),
            guard=ExecutionGuardResult(False, "local path does not exist"),
            strategy=StrategySelection("reject", "local path does not exist"),
            decision=Decision(False, "local path does not exist", StrategySelection("reject", "local path does not exist")),
            trace=trace,
            packet=None,
            block_reason="local path does not exist",
        )
    intent = analyze_intent(intake, repository_root)
    project = resolve_project(
        intent.classification,
        repository_root,
        raw_request=intake.raw_request,
        current_working_directory=current_working_directory,
        resource_project_name=resource_result.project_name,
    )
    coherence = check_coherence(project)
    strategy = select_strategy(intent.task_type, dry_run=dry_run, live_run=live_run)
    guard = guard_execution(coherence, intent.confidence)
    decision = decide(guard, strategy)

    trace = CoordinatorTrace(
        intent=intent.task_type,
        project=project.name,
        strategy=strategy.name,
        provider=project.provider,
        archiops="enabled",
        decision="blocked" if not decision.allowed else "approved",
        reason=decision.reason,
    )
    resource_trace = ResourceTrace(
        raw_input=resource_result.raw_input,
        detected_paths=resource_result.detected_paths,
        normalized_paths=resource_result.normalized_paths,
        existing_paths=resource_result.existing_paths,
        missing_paths=resource_result.missing_paths,
        blocked_paths=resource_result.blocked_paths,
        resource_types=resource_result.resource_types,
        selected_resource=resource_result.resource_trace["selected_resource"],
        intake_status=resource_result.intake_status,
    )

    if not decision.allowed:
        return CoordinatorResult(
            intake=intake,
            system_prompt=system_prompt,
            resource=resource_trace,
            intent=intent,
            project=project,
            coherence=coherence,
            guard=guard,
            strategy=strategy,
            decision=decision,
            trace=trace,
            packet=None,
            block_reason=decision.reason,
        )

    packet = build_task_packet(
        intake,
        intent.classification,
        project,
        repository_root,
        current_working_directory=current_working_directory,
    )

    return CoordinatorResult(
        intake=intake,
        system_prompt=system_prompt,
        resource=resource_trace,
        intent=intent,
        project=project,
        coherence=coherence,
        guard=guard,
        strategy=strategy,
        decision=decision,
        trace=trace,
        packet=packet,
    )
