"""Cognitive Interface Layer for human-centered coordination."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from slypilot.contracts import (
    TechnicalRequestBrief, 
    ProjectBrief, 
    TechnicalResponsePacket, 
    IntentType,
    TechnicalBriefInvalid,
    safe_project_label
)
from slypilot.tools.filesystem.path_detector import detect_paths


class CognitiveInterface:
    def __init__(self, repository_root: Path) -> None:
        self.repository_root = repository_root
        prompt_path = repository_root / "slypilot" / "cognitive" / "cognitive_prompt.md"
        if prompt_path.exists():
            self._prompt = prompt_path.read_text(encoding="utf-8")
        else:
            self._prompt = "ROLE: Interface Cognitive de SlyPilot. PRINCIPES: Comprendre, Reformuler, Guider."

    def classify_intent(self, user_input: str, active_project: dict[str, Any] | None = None) -> IntentType:
        """Classify the user's message into a discrete intent type."""
        lowered = user_input.lower().strip()
        
        if lowered in {"bonjour", "salut", "hello", "bonsoir", "coucou"}:
            return IntentType.GREETING
            
        if lowered in {"ok", "okay", "next", "continue", "continuer", "vas-y", "vas y", "go", "oui", "yes", "y"}:
            return IntentType.WORKFLOW_CONTINUE

        if any(q in lowered for q in ("pourquoi", "je ne comprend", "explique", "c'est quoi", "c est quoi", "info", "aide", "help")):
            return IntentType.PEDAGOGY_REQUEST

        from slypilot.classifier import _has_technical_signal

        # Priority 1: Explicit Technical Signal (Analysis, Bug, etc.)
        if _has_technical_signal(lowered):
            return IntentType.TECHNICAL_REQUEST

        # Priority 2: Correction detection (Refined triggers)
        correction_triggers = [
            "c'est ce projet", "je parlais de", "je parlais du", "je t'ai demandé", "non c'est", 
            "voilà le chemin", "voici le chemin", "le chemin est"
        ]
        if any(t in lowered for t in correction_triggers):
            return IntentType.CORRECTION_PROJECT

        if active_project and ("comprendre" in lowered or "bug" in lowered or "architecture" in lowered):
             return IntentType.TECHNICAL_REQUEST

        return IntentType.HUMAN_QUESTION

    def qualify_intent(self, user_input: str | None, intent_type: IntentType, active_project: dict[str, Any] | None = None) -> str | TechnicalRequestBrief | None:
        """
        Qualify the user's intent.
        Returns a string (question/response), a TechnicalRequestBrief if a technical call is needed,
        or None if legacy fallback is required.
        """
        raw_text = user_input or ""
        lowered = raw_text.lower().strip()

        if intent_type == IntentType.GREETING:
            return "Bonjour. Je suis SlyPilot. Comment puis-je vous aider sur vos projets techniques aujourd'hui ?"

        if intent_type == IntentType.PEDAGOGY_REQUEST:
            return self._generate_pedagogical_explanation(raw_text, active_project)

        if intent_type == IntentType.HUMAN_QUESTION:
            if not active_project:
                return "Je suis là pour vous aider à naviguer dans vos projets techniques. Avez-vous un dossier ou un projet spécifique à analyser ?"
            project_label = safe_project_label(active_project)
            return f"Je reste à votre disposition pour toute question sur le projet {project_label}."

        if intent_type == IntentType.CLARIFICATION:
             from slypilot.ui.guidance_renderer import render_analysis_discovery
             project_label = safe_project_label(active_project)
             return render_analysis_discovery(project_label, "general", include_header=False)

        if intent_type == IntentType.WORKFLOW_CONTINUE:
             return self._handle_continuation(active_project)

        if intent_type == IntentType.TECHNICAL_REQUEST:
             detected_paths = detect_paths(raw_text)
             if detected_paths:
                 project_path = detected_paths[0].normalized_path
                 project_name = Path(project_path).name
                 project_data = {"name": project_name, "path": project_path}
                 return self._signal_technical_request(raw_text, project_data)

             if active_project:
                 return self._signal_technical_request(raw_text, active_project)

             return (
                 "Oui, je peux lancer l’analyse, mais il me manque encore le chemin local du projet.\n"
                 "Partagez simplement votre projet avec son chemin local, par exemple :\n"
                 "analyse /Users/.../MonProjet"
             )

        return None

    def translate_response(self, packet: TechnicalResponsePacket) -> str:
        """Translate technical findings into pedagogical human language."""
        from .response_translator import translate_technical_response
        return translate_technical_response(packet)

    def _handle_continuation(self, active_project: dict[str, Any] | None) -> str:
        """Handle conversational signals like 'ok' or 'continue'."""
        if not active_project:
            return "Sur quel projet souhaitez-vous travailler ?"

        project_label = safe_project_label(active_project)
        return (
            f"L'analyse de {project_label} est disponible. "
            f"Que souhaitez-vous explorer ensuite : bug, architecture ou documentation ?"
        )

    def _signal_technical_request(self, user_input: str, active_project: dict[str, Any] | None) -> TechnicalRequestBrief:
        """Build a preliminary brief to signal technical intent."""
        from slypilot.coordinator.technical_brief_builder import build_technical_brief
        return build_technical_brief(user_input, active_project or {"name": "unknown", "path": ""})

    def _generate_pedagogical_explanation(self, user_input: str, active_project: dict[str, Any] | None) -> str:
        lowered = user_input.lower()
        if "docker" in lowered:
            return "Docker est un outil qui permet d'emballer une application et ses dépendances dans un réceptacle isolé (un conteneur). Cela garantit que le projet fonctionnera de la même manière sur n'importe quelle machine."
        if "archi ops" in lowered or "archiops" in lowered:
            return "ARCHI OPS est la cartographie technique utilisée par SlyPilot pour comprendre un projet sans avoir à tout rescanner à chaque fois."
        
        if active_project:
            project_label = safe_project_label(active_project)
            return f"Je suis là pour vous aider à comprendre le projet {project_label}. Vous pouvez me poser des questions sur son architecture ou ses dépendances."
            
        return "Je suis là pour vous aider à naviguer dans la complexité technique de vos projets. Posez-moi vos questions !"
