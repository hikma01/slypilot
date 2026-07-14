"""Render technical traces separately from UX messages."""

from __future__ import annotations

from .style import hr, dim


def render_resource_trace(resource_trace: object) -> str:
    trace = resource_trace.to_dict() if hasattr(resource_trace, "to_dict") else dict(resource_trace)
    selected = trace.get("selected_resource", {})
    if isinstance(selected, str):
        selected = {"path": selected}
    lines = [
        hr(),
        "📋 RESOURCE TRACE",
        hr(),
        "",
        f"raw_input: {trace.get('raw_input', '')}",
        f"detected_paths: {', '.join(trace.get('detected_paths', [])) or 'none'}",
        f"normalized_paths: {', '.join(trace.get('normalized_paths', [])) or 'none'}",
        f"existing_paths: {', '.join(trace.get('existing_paths', [])) or 'none'}",
        f"missing_paths: {', '.join(trace.get('missing_paths', [])) or 'none'}",
        f"blocked_paths: {', '.join(trace.get('blocked_paths', [])) or 'none'}",
        f"resource_types: {', '.join(trace.get('resource_types', [])) or 'none'}",
        f"selected_resource: {selected}",
        f"intake_status: {trace.get('intake_status', '')}",
    ]
    return dim("\n".join(lines))


def render_coordinator_trace(trace: object) -> str:
    data = trace.to_dict() if hasattr(trace, "to_dict") else dict(trace)
    advisory = data.get("advisory", {})
    intent_trace = data.get("intent_trace", {})
    lines = [
        hr(),
        "🧠 COORDINATOR TRACE",
        hr(),
        "",
        f"intent           : {data.get('intent', '')}",
        f"project          : {data.get('project', '')}",
        f"strategy         : {data.get('strategy', '')}",
        f"skill            : {data.get('skill', '')}",
        f"provider         : {data.get('provider', '')}",
        f"archiops         : {data.get('archiops', '')}",
        f"decision         : {data.get('decision', '')}",
        f"reason           : {data.get('reason', '')}",
        f"dry_run          : {str(data.get('dry_run', False)).lower()}",
        f"live_run         : {str(data.get('live_run', False)).lower()}",
        f"provider_called  : {str(data.get('provider_called', False)).lower()}",
    ]
    if intent_trace:
        lines.extend(
            [
                "",
                "INTENT_TRACE",
                f"raw_input         : {intent_trace.get('raw_input', '')}",
                f"normalized_input  : {intent_trace.get('normalized_input', '')}",
                f"detected_action_terms: {', '.join(intent_trace.get('detected_action_terms', [])) or 'none'}",
                f"detected_intent   : {intent_trace.get('detected_intent', '')}",
                f"intent_confidence : {intent_trace.get('intent_confidence', '')}",
                f"detected_paths    : {', '.join(intent_trace.get('detected_paths', [])) or 'none'}",
                f"resource_type     : {intent_trace.get('resource_type', '')}",
                f"project_name      : {intent_trace.get('project_name', '')}",
                f"fusion_result     : {intent_trace.get('fusion_result', '')}",
                f"final_decision    : {intent_trace.get('final_decision', '')}",
                f"ambiguity_reason  : {intent_trace.get('ambiguity_reason', '')}",
            ]
        )
    if advisory:
        lines.extend(
            [
                "",
                "ADVISORY_TRACE",
                f"advisory            : {advisory.get('advisory', '')}",
                f"diagnosis           : {advisory.get('diagnosis', '')}",
                f"capability_level     : {advisory.get('capability_level', '')}",
                f"recommended_action   : {advisory.get('recommended_action', '')}",
                f"alternatives         : {', '.join(advisory.get('alternatives', [])) or 'none'}",
                f"recommendation_reason: {advisory.get('recommendation_reason', '')}",
                f"confidence           : {advisory.get('confidence', '')}",
            ]
        )
    return dim("\n".join(lines))
