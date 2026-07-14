"""Shared contracts for Cognitive <-> Technical coordination."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any
from datetime import datetime, timezone


def get_project_path(project: Any) -> str | None:
    """Robustly retrieve the project path from various project-related objects."""
    if project is None:
        return None

    if isinstance(project, dict):
        return str(
            project.get("path")
            or project.get("project_path")
            or project.get("root_path")
            or ""
        )

    return str(
        getattr(project, "path", None)
        or getattr(project, "project_path", None)
        or getattr(project, "root_path", None)
        or ""
    )


def safe_project_label(project: Any) -> str:
    """Get a human-friendly project name, deducing it from path if necessary."""
    if not project:
        return "votre projet"

    if isinstance(project, dict):
        name = (
            project.get("name")
            or project.get("project_name")
            or project.get("project")
            or project.get("project_id")
        )
    else:
        name = getattr(project, "name", None)
    if name and str(name).strip().lower() not in {"unknown", "none", "null", "undefined", ""}:
        return str(name).strip()

    path = get_project_path(project)
    if path:
        return Path(path).name

    return "votre projet"


def get_project_name(project: Any) -> str:
    """Robustly retrieve the project name from a project object or dict."""
    if project is None:
        return "unknown"

    if isinstance(project, dict):
        return str(project.get("name") or project.get("project_name") or "unknown")

    return str(
        getattr(project, "name", None)
        or getattr(project, "project_name", None)
        or "unknown"
    )


class IntentType(Enum):
    HUMAN_QUESTION = auto()
    TECHNICAL_REQUEST = auto()
    WORKFLOW_CONTINUE = auto()
    CLARIFICATION = auto()
    PEDAGOGY_REQUEST = auto()
    CORRECTION_PROJECT = auto()
    GREETING = auto()
    UNKNOWN = auto()


class TechnicalBriefInvalid(Exception):
    """Raised when a TechnicalRequestBrief is missing mandatory fields."""


@dataclass(frozen=True)
class ProjectBrief:
    name: str
    path: str


@dataclass(frozen=True)
class TechnicalRequestBrief:
    user_goal: str
    project: ProjectBrief | dict[str, str]
    analysis_type: str = "global_understanding"
    user_profile: dict[str, Any] = field(default_factory=lambda: {
        "technical_level": "non_developer",
        "needs_pedagogy": True,
    })
    requested_output: dict[str, Any] = field(default_factory=lambda: {
        "format": "pedagogical_summary",
        "include_visual_tree": True,
        "include_recommendation": True,
    })
    constraints: dict[str, Any] = field(default_factory=lambda: {
        "avoid_jargon": True,
        "no_provider_call_without_need": True,
        "bounded_analysis": True,
    })
    questions_to_answer: list[str] = field(default_factory=list)

    def get_project_path(self) -> str:
        if isinstance(self.project, dict):
            return str(self.project.get("path", ""))
        return str(getattr(self.project, "path", ""))

    def get_project_name(self) -> str:
        if isinstance(self.project, dict):
            return str(self.project.get("name", "unknown"))
        return str(getattr(self.project, "name", "unknown"))

    def validate(self) -> None:
        if not self.get_project_path():
            raise TechnicalBriefInvalid("Mandatory project path is missing.")
        if not self.get_project_name():
            raise TechnicalBriefInvalid("Mandatory project name is missing.")
        if not self.user_goal:
            raise TechnicalBriefInvalid("User goal is required.")
        if not self.analysis_type:
            raise TechnicalBriefInvalid("Analysis type is required.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class PendingAction:
    action_id: str
    action_type: str
    project_path: str
    project_name: str
    source_message: str
    status: str = "pending"  # pending, running, completed, failed
    stage: str = "initial"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TechnicalResponsePacket:
    project_name: str
    project_path: str
    status: str  # success, partial, failed
    stack_detected: bool
    technologies: list[str]
    architecture_summary: str
    business_summary: str
    risks: list[str]
    generated_files: list[str]
    raw_references: list[dict[str, Any]]
    metadata: dict[str, Any]
    errors: list[str]
    recommendation: str = ""  # Keep for compatibility with existing pedagogical logic

    def validate(self) -> bool:
        """Validate that the packet contains minimum viable information for STI 2."""
        if not self.project_name:
            return False
        if not self.project_path:
            return False
        if self.status not in ["success", "partial", "failed"]:
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)



@dataclass(frozen=True)
class WorkflowState:
    workflow_id: str
    status: str
    current_phase: str | None
    completed_phases: list[str] = field(default_factory=list)
    remaining_phases: list[str] = field(default_factory=list)
    last_response_id: str | None = None
    awaiting_user_confirmation: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
