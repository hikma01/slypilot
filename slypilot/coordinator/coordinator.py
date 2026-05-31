"""Central coordinator for SlyPilot V2."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from slypilot.archi_ops_loader import load_archi_ops_context
from slypilot.intake import Intake
from slypilot.project_resolver import ResolvedProject, resolve_project
from slypilot.task_packet_builder import BuiltPacket, build_task_packet

from .coherence_checker import CoherenceResult, check_coherence
from .decision_engine import Decision, decide
from .execution_guard import ExecutionGuardResult, guard_execution
from .intent_analyzer import IntentAnalysis, analyze_intent
from .coordinator_trace import CoordinatorTrace
from .prompt_loader import load_coordinator_prompt
from .strategy_selector import StrategySelection, select_strategy


@dataclass(frozen=True)
class CoordinatorResult:
    intake: Intake
    system_prompt: str
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
    intent = analyze_intent(intake, repository_root)
    project = resolve_project(
        intent.classification,
        repository_root,
        raw_request=intake.raw_request,
        current_working_directory=current_working_directory,
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

    if not decision.allowed:
        return CoordinatorResult(
            intake=intake,
            system_prompt=system_prompt,
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
        intent=intent,
        project=project,
        coherence=coherence,
        guard=guard,
        strategy=strategy,
        decision=decision,
        trace=trace,
        packet=packet,
    )
