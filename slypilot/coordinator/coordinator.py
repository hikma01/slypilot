"""Central coordinator for SlyPilot V2."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from slypilot.archi_ops_loader import load_archi_ops_context
from slypilot.intake import Intake, build_intake
from slypilot.resource_resolver import resolve_resources
from slypilot.project_resolver import ResolvedProject, resolve_project
from slypilot.project import ProjectMemoryStore, prepare_project
from slypilot.task_packet_builder import BuiltPacket, build_task_packet
from slypilot.classifier import classify_intake, _has_technical_signal

from .coherence_checker import CoherenceResult, check_coherence
from .decision_engine import Decision, decide
from .execution_guard import ExecutionGuardResult, guard_execution
from .intent_analyzer import IntentAnalysis, analyze_intent, resolve_intent_with_resource
from .expert_interpreter import ExpertDiagnostic, interpret_expert_diagnostic
from .coordinator_trace import AdvisoryTrace, CoordinatorTrace, ResourceTrace
from .strategy_selector import StrategySelection, select_strategy
from .prompt_loader import load_coordinator_prompt


@dataclass(frozen=True)
class CoordinatorResult:
    intent: Any
    project: ResolvedProject
    resource: object
    strategy: Any
    decision: Decision
    coherence: CoherenceResult | None
    guard: ExecutionGuardResult | None
    trace: CoordinatorTrace
    system_prompt: str = ""
    packet: BuiltPacket | None = None
    diagnostic: ExpertDiagnostic | None = None
    archi_ops: Any | None = None
    block_reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "intent": self.intent.to_dict() if hasattr(self.intent, "to_dict") else str(self.intent),
            "project": self.project.to_dict(),
            "resource": self.resource.to_dict() if hasattr(self.resource, "to_dict") else str(self.resource),
            "strategy": self.strategy.to_dict() if hasattr(self.strategy, "to_dict") else str(self.strategy),
            "decision": self.decision.to_dict(),
            "coherence": self.coherence.to_dict() if hasattr(self.coherence, "to_dict") else str(self.coherence),
            "guard": self.guard.to_dict() if hasattr(self.guard, "to_dict") else str(self.guard),
            "trace": self.trace.to_dict(),
            "packet": self.packet.to_dict() if self.packet else None,
            "diagnostic": self.diagnostic.to_dict() if self.diagnostic else None,
            "archi_ops": self.archi_ops.to_dict() if hasattr(self.archi_ops, "to_dict") else str(self.archi_ops),
        }


def coordinate_request(
    intake: Intake,
    repository_root: Path,
    current_working_directory: Path | None = None,
    active_project_name: str | None = None,
    dry_run: bool = False,
    live_run: bool = False,
) -> CoordinatorResult:
    system_prompt = load_coordinator_prompt(repository_root / "prompts" / "coordinator")
    resource_result = resolve_resources(intake.raw_request, current_working_directory or Path.cwd())
    
    # Priority 1: Security and Access Guard
    if resource_result.intake_status == "blocked":
        trace = CoordinatorTrace(
            intent="blocked",
            project="unknown",
            strategy="reject",
            provider="none",
            archiops="disabled",
            decision="blocked",
            reason="sensitive path blocked",
            intent_trace={"block_reason": "sensitive path"},
        )
        return CoordinatorResult(
            intent=IntentAnalysis(task_type="blocked", confidence="high", classification=None), # type: ignore
            project=ResolvedProject(name="unknown", provider="none", environment="none", path="", status="blocked", resolution_source="guard"),
            resource=resource_result,
            strategy=None,
            decision=Decision(False, "sensitive path blocked", None), # type: ignore
            coherence=None,
            guard=None,
            trace=trace,
            system_prompt=system_prompt,
            packet=None,
            block_reason="sensitive path blocked",
        )

    # Priority 2: Missing local path detection
    if resource_result.intake_status == "missing_path":
        trace = CoordinatorTrace(
            intent="blocked",
            project="unknown",
            strategy="reject",
            provider="none",
            archiops="enabled",
            intent_trace={"block_reason": "local path does not exist"},
            decision="blocked",
            reason="local path does not exist",
        )
        return CoordinatorResult(
            intent=IntentAnalysis(task_type="blocked", confidence="high", classification=None), # type: ignore
            project=ResolvedProject(name="unknown", provider="none", environment="none", path="", status="missing_path", resolution_source="resolver"),
            resource=resource_result,
            strategy=None,
            decision=Decision(False, "local path does not exist", None), # type: ignore
            coherence=None,
            guard=None,
            trace=trace,
            system_prompt=system_prompt,
            packet=None,
            block_reason="local path does not exist",
        )
        
    intent = analyze_intent(intake, repository_root)
    project = resolve_project(
        intent.classification,
        repository_root,
        intake.raw_request,
        current_working_directory or Path.cwd(),
        resource_result.project_name,
        active_project_name,
        resource_path=resource_result.project_root,
    )
    
    # Resolve intent details based on project and resources
    intent_fusion = resolve_intent_with_resource(intake, resource_result)
    
    # Strategy selection
    strategy = select_strategy(intent_fusion.detected_intent, dry_run=dry_run, live_run=live_run)

    # Execution Guard
    coherence = check_coherence(project)
    guard = guard_execution(coherence, intent.confidence)

    # Execution Decision
    decision = decide(guard, strategy)
    if not coherence.allowed and project.status == "ambiguous":
        strategy = StrategySelection("ask_clarification", intent_fusion.ambiguity_reason or "multiple_candidates")
        decision = Decision(False, "multiple local paths detected", strategy)
    elif intent_fusion.final_decision == "ask_project_action_choice":
        strategy = StrategySelection("ask_clarification", intent_fusion.ambiguity_reason or "clarification_required")
        decision = Decision(False, intent_fusion.ambiguity_reason or "project path without action verb", strategy)
    elif intent_fusion.final_decision in {"block_missing_path", "block_sensitive_path"}:
        decision = Decision(False, intent_fusion.ambiguity_reason or decision.reason, strategy)

    # Build Archi Ops Context
    from slypilot.contracts import get_project_path
    project_path = get_project_path(project)
    bootstrap_target = resource_result.project_root or project_path
    if bootstrap_target and resource_result.project_root:
        preparation = prepare_project(bootstrap_target)
        if preparation.preparation_status in {"success", "already_ready"}:
            project_path = preparation.project_path
    
    # Use the technical task_type from classification for ArchiOps loading
    archi_ops = load_archi_ops_context(
        repository_root,
        project.name,
        intent.task_type,
        "standard",
        Path(project_path) if project_path else None
    )
    
    # Technical Packet Generation (if allowed)
    packet = None
    diagnostic = None
    skill = _select_skill(intent.task_type, intent_fusion, resource_result)
    if decision.allowed:
        packet = build_task_packet(
            intake,
            intent.classification,
            project,
            repository_root,
            current_working_directory=Path(project_path) if project_path else None
        )
        
        # Expert interpretation of technical facts
        diagnostic = interpret_expert_diagnostic(project.name, packet.metadata)

        if packet is not None:
            project_memory_store = ProjectMemoryStore(repository_root)
            project_memory = project_memory_store.upsert_from_analysis(
                project_name=getattr(packet, "project_name", None) or project.name,
                project_path=str(getattr(packet, "project_path", "") or project_path or ""),
                knowledge_contract=archi_ops.knowledge_contract if archi_ops else None,
                diagnostic=diagnostic,
                packet=packet,
            )
            packet.metadata["project_memory"] = project_memory.to_dict()
            packet_project_path = str(getattr(packet, "project_path", "") or project_path or "")
            packet.metadata["project_memory_signature"] = project_memory_store.project_signature(packet_project_path)

    trace = CoordinatorTrace(
        intent=intent_fusion.detected_intent,
        project=project.name,
        strategy=strategy.name,
        skill=skill,
        provider="local",
        archiops="enabled" if archi_ops.is_present else "disabled",
        decision=decision.reason if decision.allowed else "blocked",
        reason=decision.reason,
        dry_run=dry_run,
        live_run=live_run,
        provider_called=bool(live_run and decision.allowed and packet is not None),
        intent_trace=intent_fusion.to_dict(),
        resource_trace=resource_result.resource_trace,
    )

    if packet is not None:
        packet.metadata["resource_trace"] = (
            resource_result.resource_trace.to_dict()
            if hasattr(resource_result.resource_trace, "to_dict")
            else resource_result.resource_trace
        )
        packet.metadata["coordinator_trace"] = trace.to_dict()
    
    return CoordinatorResult(
        intent=intent_fusion,
        project=project,
        resource=resource_result,
        strategy=strategy,
        decision=decision,
        coherence=coherence,
        guard=guard,
        trace=trace,
        system_prompt=system_prompt,
        packet=packet,
        diagnostic=diagnostic,
        archi_ops=archi_ops,
        block_reason=None if decision.allowed else decision.reason,
    )


from slypilot.contracts import (
    TechnicalRequestBrief, 
    TechnicalResponsePacket, 
    TechnicalBriefInvalid,
    get_project_path,
    get_project_name
)

def handle_technical_brief(
    brief: TechnicalRequestBrief, 
    repository_root: Path, 
    raw_request: str | None = None
) -> TechnicalResponsePacket:
    """Entry point for the Technical Coordination layer."""
    brief_project_path = brief.get_project_path()
    brief_project_name = brief.get_project_name()

    rules_candidates = [repository_root / "projects.yaml", repository_root / "rules.yaml"]
    if not any(candidate.exists() for candidate in rules_candidates):
        return TechnicalResponsePacket(
            project_name=brief_project_name,
            project_path=brief_project_path,
            status="partial",
            stack_detected=False,
            technologies=[],
            architecture_summary="Structure globale cartographiée.",
            business_summary="Cœur métier en cours d'identification.",
            risks=[],
            generated_files=[],
            raw_references=[],
            metadata={
                "selected_maps": [],
                "knowledge_contract": None,
                "project_yaml_loaded": False,
                "project_contract_injected": False,
            },
            errors=["ArchiOps rules missing."],
            recommendation="Explorer l'arborescence métier.",
        )

    # Priority: preserve the original technical request when it already carries signal,
    # otherwise synthesize a technical request from the validated brief.
    if raw_request and _has_technical_signal(raw_request.lower()):
        request_text = raw_request
    else:
        request_text = f"analyse {brief_project_path or brief_project_name}"
    intake = build_intake(request_text, repository_root)
    
    # Use coordinate_request to handle ALL the logic (resolution, guard, execution)
    # We set dry_run=False to actually perform the analysis and get a diagnostic
    result = coordinate_request(
        intake,
        repository_root,
        active_project_name=get_project_name(brief),
        dry_run=False,
        live_run=False
    )
    
    # Validate that we at least found a project
    if result.project.status == "needs_project_path" or not get_project_path(result.project):
         raise TechnicalBriefInvalid("Project path could not be resolved by the technical layer.")

    # Map TC results to the new TechnicalResponsePacket contract (STI 2)
    diagnostic = result.diagnostic
    packet_meta = result.packet.metadata if result.packet else {}
    archi_result = result.archi_ops
    project_path = get_project_path(result.project)
    project_name = brief_project_name or result.project.name

    # Extract data from ArchiOps Loader
    technologies = getattr(diagnostic, "detected_technologies", []) if diagnostic else []
    if not technologies:
        technologies = getattr(diagnostic, "technologies", []) if diagnostic else []
        
    architecture_summary = ""
    business_summary = ""
    risks = []
    generated_files = []
    
    if archi_result and archi_result.knowledge_contract:
        kc = archi_result.knowledge_contract
        if kc.repo_map: architecture_summary = kc.repo_map.content
        if kc.business_map: business_summary = kc.business_map.content
        if kc.interpreted_tree: generated_files.append(kc.interpreted_tree.path)
        if kc.semantic_index: generated_files.append(kc.semantic_index.path)
        
    if diagnostic:
        if not architecture_summary and diagnostic.summary:
            architecture_summary = "\n".join(diagnostic.summary)
        risks = getattr(diagnostic, "risks", [])
        if not risks and hasattr(diagnostic, "meaning"):
            risks = [m for m in diagnostic.meaning if "risque" in m.lower() or "limite" in m.lower()]

    errors = result.trace.reason if not result.decision.allowed else ""
    all_errors = [errors] if errors else []
    if not result.packet:
        all_errors.append("ArchiOps n'a pas retourné de cartographie exploitable.")

    resolved_project_name = project_name or brief_project_name
    if resolved_project_name in {"", "none", "unknown", None}:  # type: ignore[comparison-overlap]
        resolved_project_name = result.project.name

    resolved_project_path = project_path or brief_project_path

    return TechnicalResponsePacket(
        project_name=resolved_project_name,
        project_path=resolved_project_path,
        status="success" if result.decision.allowed and result.packet else "partial",
        stack_detected=bool(technologies),
        technologies=technologies,
        architecture_summary=architecture_summary or "Structure globale cartographiée.",
        business_summary=business_summary or "Cœur métier en cours d'identification.",
        risks=risks,
        generated_files=generated_files,
        raw_references=packet_meta.get("selected_maps", []), # type: ignore
        metadata=packet_meta,
        errors=all_errors,
        recommendation=diagnostic.recommendation if diagnostic else "Explorer l'arborescence métier."
    )


def _select_skill(task_type: str, intent_fusion: object, resource_result: object, blocked: bool = False) -> str:
    if blocked:
        return "explanation_skill"
    normalized_task = str(task_type or "").lower()
    if normalized_task in {"architecture", "cartography"}:
        return "cartography_skill"
    if normalized_task in {"analyze_project", "debug", "patch", "review"}:
        return "project_analysis_skill"
    if normalized_task in {"explain", "explanation"}:
        return "explanation_skill"
    if normalized_task in {"risk", "risk_analysis"}:
        return "risk_analysis_skill"
    fusion_result = str(getattr(intent_fusion, "fusion_result", "")).lower()
    if any(term in fusion_result for term in ("pourquoi", "explique", "je ne comprends pas", "c'est quoi")):
        return "explanation_skill"
    if "risk" in fusion_result:
        return "risk_analysis_skill"
    return "explanation_skill"
