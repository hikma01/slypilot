"""Pending action resolution for conversation runtime."""

from __future__ import annotations

from dataclasses import dataclass

from .response_normalizer import normalize_response


@dataclass(frozen=True)
class PendingActionExecution:
    handled: bool
    action: str | None
    keep_pending_action: bool
    normalized_response: str


class PendingActionExecutor:
    def _pending_type(self, pending_action: dict[str, object] | None) -> str:
        if not isinstance(pending_action, dict):
            return ""
        return str(
            pending_action.get("type")
            or pending_action.get("action_type")
            or pending_action.get("pending_type")
            or ""
        )

    def _is_natural_conversation(self, text: str) -> str | None:
        """Detect natural conversation to route to intent classifier or conversational fallback."""
        lowered = text.lower().strip()
        # Explanations/questions
        if lowered in {"pourquoi", "pourquoi ?", "pourquoi?", "explique", "explique moi", "explique-moi", "je ne comprends pas", "je ne comprend pas", "?"}:
            return "question"
        # Greetings
        if lowered in {"bonjour", "salut", "coucou", "hello", "hi"}:
            return "greeting"
        # Explicit continued actions that are natural but might mean "proceed"
        if lowered in {"ok", "oui", "vas-y", "vas y", "continue", "next", "d'accord", "d accord"}:
            return "proceed"
        # Disagreement / explicit stop
        if lowered in {"non", "stop", "arrête", "arrete"}:
            return "cancel"
        return None

    def resolve(self, raw: str, pending_action: dict[str, object] | None) -> PendingActionExecution:
        normalized = normalize_response(raw)
        
        # Axe 1: INTENT avant ETAT (detect natural language first)
        conversation_intent = self._is_natural_conversation(raw)
        if conversation_intent:
            if conversation_intent == "question":
                return PendingActionExecution(True, "question", True, normalized)
            if conversation_intent == "greeting":
                return PendingActionExecution(True, "greeting", True, normalized)
            if conversation_intent == "proceed":
                if not pending_action:
                    return PendingActionExecution(True, "proceed", False, normalized)
                pending_type = self._pending_type(pending_action)
                if pending_type in {"init_required", "init_archiops"}:
                    return PendingActionExecution(True, "prepare_project", False, normalized)
                if pending_type == "analysis_plan":
                    return PendingActionExecution(True, "start_analysis", False, normalized)
                return PendingActionExecution(True, "proceed", False, normalized)
            if conversation_intent == "cancel":
                return PendingActionExecution(True, "cancel", False, normalized)

        if not pending_action:
            return PendingActionExecution(False, None, False, normalized)

        pending_type = self._pending_type(pending_action)

        if pending_type == "analysis_discovery":
            # For analysis_discovery, any textual input should be interpreted as the user's focus
            return PendingActionExecution(True, "provide_focus", False, raw)

        if pending_type == "analysis_plan":
            if normalized == "confirm" or conversation_intent == "proceed":
                return PendingActionExecution(True, "start_analysis", False, normalized)
            if normalized == "cancel" or conversation_intent == "cancel":
                return PendingActionExecution(True, "cancel", False, normalized)
            return PendingActionExecution(False, None, True, normalized)

        if pending_type in {"clarification", "choose_next_action"}:
            if normalized == "info":
                return PendingActionExecution(True, "info", True, normalized)
            if normalized == "cancel":
                return PendingActionExecution(True, "cancel", False, normalized)
            if normalized in {"option_1", "option_2", "option_3"}:
                mapping = {
                    "option_1": "analyze_project",
                    "option_2": "minimal_project_scan",
                    "option_3": "cancel",
                }
                keep_pending = normalized == "option_3"
                return PendingActionExecution(True, mapping[normalized], keep_pending, normalized)
            if normalized in {"confirm", "option_1"}:
                return PendingActionExecution(True, "analyze_project", False, normalized)
            return PendingActionExecution(False, None, True, normalized)

        if pending_type == "post_diagnostic_next_step":
            stage = str(pending_action.get("stage", "initial"))
            if stage == "followup":
                if normalized in {"option_1", "option_2", "option_3"}:
                    mapping = {
                        "option_1": "show_cartography",
                        "option_2": "enrich_cartography",
                        "option_3": "stop_here",
                    }
                    keep_pending = normalized != "option_3"
                    return PendingActionExecution(True, mapping[normalized], keep_pending, normalized)
                if normalized == "cancel":
                    return PendingActionExecution(True, "stop_here", False, normalized)
                return PendingActionExecution(False, None, True, normalized)
            if normalized in {"option_1", "option_2", "option_3", "option_4"}:
                mapping = {
                    "option_1": "analyze_files",
                    "option_2": "show_map",
                    "option_3": "find_risks",
                    "option_4": "cancel",
                }
                keep_pending = normalized == "option_4"
                return PendingActionExecution(True, mapping[normalized], keep_pending, normalized)
            if normalized == "cancel":
                return PendingActionExecution(True, "cancel", False, normalized)
            return PendingActionExecution(False, None, True, normalized)

        if pending_type in {"init_required", "init_archiops"}:
            if normalized == "info":
                return PendingActionExecution(True, "info", True, normalized)
            if normalized == "confirm":
                return PendingActionExecution(True, "prepare_project", False, normalized)
            if normalized == "cancel":
                return PendingActionExecution(True, "cancel", False, normalized)
            return PendingActionExecution(False, None, True, normalized)

        return PendingActionExecution(False, None, False, normalized)
