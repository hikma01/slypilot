"""Compatibility exports for shared STI contracts.

Contracts now live in ``slypilot.contracts`` so the technical layer does not
depend on the cognitive package. This module remains for older imports.
"""

from slypilot.contracts import (
    IntentType,
    ProjectBrief,
    TechnicalBriefInvalid,
    TechnicalRequestBrief,
    TechnicalResponsePacket,
    WorkflowState,
    get_project_name,
    get_project_path,
    safe_project_label,
)

__all__ = [
    "IntentType",
    "ProjectBrief",
    "TechnicalBriefInvalid",
    "TechnicalRequestBrief",
    "TechnicalResponsePacket",
    "WorkflowState",
    "get_project_name",
    "get_project_path",
    "safe_project_label",
]
