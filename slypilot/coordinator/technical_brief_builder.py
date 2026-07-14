"""Helper to build validated TechnicalRequestBrief for STI V1."""

from __future__ import annotations
from pathlib import Path
from typing import Any

from slypilot.contracts import TechnicalRequestBrief, ProjectBrief


def build_technical_brief(
    user_input: str, 
    project_data: dict[str, str] | ProjectBrief
) -> TechnicalRequestBrief:
    """Build a TechnicalRequestBrief from user input and project data."""
    goal = "compréhension globale"
    lowered = user_input.lower()
    
    if "bug" in lowered:
        goal = "recherche de bug"
    elif "architecture" in lowered:
        goal = "audit architecture"
    elif "synthèse" in lowered or "synthese" in lowered:
        goal = "synthèse finale"

    brief = TechnicalRequestBrief(
        user_goal=goal,
        project=project_data,
        analysis_type="global_understanding" if goal == "compréhension globale" else goal,
        questions_to_answer=["Que fait ce projet ?", "Où est le cœur métier ?"]
    )
    
    return brief


def validate_technical_brief(brief: TechnicalRequestBrief) -> None:
    """Validate a technical brief. Raises TechnicalBriefInvalid if incomplete."""
    brief.validate()


def get_project_path(brief: TechnicalRequestBrief) -> str:
    """Robustly retrieve the project path from a brief."""
    return brief.get_project_path()


def get_project_name(brief: TechnicalRequestBrief) -> str:
    """Robustly retrieve the project name from a brief."""
    return brief.get_project_name()
