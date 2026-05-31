"""Conversation guidance renderer for SlyPilot."""

from __future__ import annotations

from .chat_renderer import render_slypilot_message


def render_greeting_prompt() -> str:
    return render_slypilot_message(
        "Bonjour.",
        [
            "Je peux t'aider à :",
            "",
            "- analyser un projet",
            "- comprendre un bug",
            "- explorer une architecture",
            "- initialiser ARCHI OPS",
            "- reprendre une session",
            "",
            "Exemple :",
            "analyse le projet /Users/.../MonProjet",
        ],
    )


def render_archiops_explanation(project_name: str) -> str:
    return render_slypilot_message(
        "ARCHI OPS",
        [
            "ARCHI OPS est la cartographie technique utilisée par SlyPilot.",
            "",
            "Elle permet à SlyPilot de comprendre un projet sans scanner tout le dépôt à chaque demande.",
            "",
            "ARCHI OPS contient notamment :",
            "",
            "- project.yaml",
            "- repo-map.md",
            "- runtime-map.md",
            "- dependency-map.md",
            "- semantic-index.md",
            "",
            "But :",
            "donner au coordinateur un contexte fiable, borné et réutilisable.",
            "",
            f"Sans ARCHI OPS, SlyPilot peut voir le dossier {project_name}, mais ne dispose pas encore du contexte suffisant pour analyser proprement.",
        ],
    )


def render_init_required_prompt(project_name: str, project_path: str) -> str:
    return render_slypilot_message(
        "Diagnostic :",
        [
            f"Projet détecté : {project_name}",
            f"Chemin : {project_path}",
            "",
            "J'ai trouvé le dossier du projet, mais ce projet n'est pas encore préparé pour l'analyse.",
            "",
            "Ma recommandation principale :",
            "initialiser ARCHI OPS pour ce projet.",
            "",
            "Pourquoi ?",
            "Cela me permettra de :",
            "",
            "- comprendre la structure du dépôt",
            "- identifier les dépendances",
            "- construire une cartographie durable",
            "- réduire les futurs temps d'analyse",
            "",
            "Cette préparation est faite une seule fois.",
            "",
            "Alternatives :",
            "",
            "[1] Recommandé :",
            "Initialiser ARCHI OPS puis analyser",
            "",
            "[2]",
            "Effectuer une analyse minimale immédiate",
            "",
            "[3]",
            "Annuler",
            "",
            "Choix conseillé :",
            "[1]",
            "",
            "Réponds :",
            "1 / 2 / 3 / [I] Info",
        ],
    )


def render_init_confirmation(project_name: str, project_path: str) -> str:
    return render_slypilot_message(
        "Confirmation reçue.",
        [
            "Action sélectionnée :",
            f"initialiser ARCHI OPS pour {project_name}.",
            "",
            "Préparation en cours...",
            "",
            "Action à exécuter :",
            f"slypilot init {project_path}",
            "",
            "Cette action n'est pas encore exécutée automatiquement par le runtime.",
        ],
    )


def render_cancel_action() -> str:
    return render_slypilot_message(
        "Action annulée.",
        [
            "Le projet reste détecté, mais aucune analyse ne sera lancée tant qu'ARCHI OPS n'est pas initialisé.",
        ],
    )


def render_info_followup() -> str:
    return render_slypilot_message(
        "Que veux-tu faire ?",
        [
            "[Y] Yes — initialiser ARCHI OPS",
            "[N] No — annuler",
            "[I] Info — expliquer ARCHI OPS",
        ],
    )


def render_ambiguity_prompt(project_name: str, project_path: str) -> str:
    return render_slypilot_message(
        "Diagnostic :",
        [
            "J'ai détecté une ressource locale, mais la demande n'est pas assez claire.",
            "",
            f"Projet détecté : {project_name}",
            f"Chemin : {project_path}",
            "",
            "Ma recommandation principale :",
            "confirmer l'objectif avant d'aller plus loin.",
            "",
            "Alternatives :",
            "",
            "1. analyser le projet",
            "2. initialiser ARCHI OPS",
            "3. afficher l’état du projet",
            "",
            "Choix conseillé :",
            "1",
            "",
            "Réponds par 1, 2 ou 3.",
        ],
    )


def render_path_missing(path: str) -> str:
    return render_slypilot_message(
        "Le chemin fourni n'existe pas.",
        [
            "Chemin :",
            path,
            "",
            "Je ne peux pas analyser une ressource absente.",
            "",
            "Vérifie le chemin puis réessaie.",
        ],
    )


def render_sensitive_path(path: str) -> str:
    return render_slypilot_message(
        "Accès refusé.",
        [
            "Ce chemin est protégé par la politique de sécurité de SlyPilot.",
            "",
            "Chemin :",
            path,
            "",
            "Raison :",
            "zone sensible bloquée.",
            "",
            "SlyPilot ne lit pas les dossiers contenant des clés, secrets ou identifiants.",
        ],
    )


def render_execution_stage(stage: str, state: str, reason: str | None = None) -> str:
    lines = [f"{stage} : {state}"]
    if reason:
        lines.extend(["", f"Raison : {reason}"])
    return render_slypilot_message("Statut d'exécution", lines)


def render_final_diagnostic(project_name: str, lines: list[str]) -> str:
    return render_slypilot_message(
        "Diagnostic initial :",
        [f"Projet : {project_name}", "", *lines],
    )


def render_analysis_restitution(
    project_name: str,
    packet_metadata: dict[str, object],
    packet_rel_path: str,
) -> str:
    def _as_list(value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value]
        return []

    selected_files = _as_list(packet_metadata.get("selected_files", []))
    selected_maps = _as_list(packet_metadata.get("selected_maps", []))
    selection_reasons = _as_list(packet_metadata.get("selection_reasons", []))
    negative_context = _as_list(packet_metadata.get("negative_context", []))
    knowledge_contract = packet_metadata.get("knowledge_contract")
    knowledge_lines: list[str] = []
    if isinstance(knowledge_contract, dict):
        def _section(title: str, value: object) -> None:
            knowledge_lines.append(title)
            if value is None:
                knowledge_lines.append("none")
                return
            if isinstance(value, dict):
                content = str(value.get("content", "")).strip()
                path = str(value.get("path", ""))
                reason = str(value.get("reason", ""))
                knowledge_lines.append(f"path: {path}")
                if reason:
                    knowledge_lines.append(f"reason: {reason}")
                knowledge_lines.append("content:")
                knowledge_lines.extend(content.splitlines() or [""])
                return
            knowledge_lines.append(str(value))

        _section("repo_map", knowledge_contract.get("repo_map"))
        knowledge_lines.append("")
        _section("runtime_map", knowledge_contract.get("runtime_map"))
        knowledge_lines.append("")
        _section("dependency_map", knowledge_contract.get("dependency_map"))
        knowledge_lines.append("")
        _section("semantic_index", knowledge_contract.get("semantic_index"))
        knowledge_lines.append("")
        important_files = knowledge_contract.get("important_files", [])
        knowledge_lines.append("important_files")
        if isinstance(important_files, list) and important_files:
            for item in important_files[:5]:
                if isinstance(item, dict):
                    knowledge_lines.append(f"- {item.get('path', '')}")
                    content = str(item.get("content", "")).strip()
                    if content:
                        knowledge_lines.extend([f"  {line}" for line in content.splitlines()[:5]])
                else:
                    knowledge_lines.append(f"- {item}")
        else:
            knowledge_lines.append("none")
    lines = [
        f"Projet : {project_name}",
        "",
        "Étapes réalisées :",
        "- préparation du projet",
        "- cartographie technique",
        "- construction du contexte",
        "- analyse bornée",
        "- restitution initiale",
        "",
        "Cartographie détectée :",
        ", ".join(selected_maps) if selected_maps else "aucune carte sélectionnée",
        "",
        "Architecture globale :",
        f"- project_yaml_loaded: {str(packet_metadata.get('project_yaml_loaded', False)).lower()}",
        f"- project_contract_injected: {str(packet_metadata.get('project_contract_injected', False)).lower()}",
        f"- context_reduction_ratio: {packet_metadata.get('context_reduction_ratio', 'none')}",
        "",
        "Fichiers clés :",
        *([f"- {path}" for path in selected_files] if selected_files else ["- aucun"]),
        "",
        "Dépendances principales :",
        *([f"- {item}" for item in negative_context] if negative_context else ["- aucune dépendance explicite détectée"]),
        "",
        "Risques ou limites visibles :",
        *([
            f"- {item}"
            for item in selection_reasons[:5]
        ] if selection_reasons else ["- aucune limite notable dans le contexte borné"]),
        "",
        "Connaissance transportée :",
        *(knowledge_lines if knowledge_lines else ["none"]),
        "",
        "Prochaine action recommandée :",
        f"- poursuivre avec le packet généré : {packet_rel_path}",
    ]
    return render_slypilot_message("Diagnostic initial :", lines)


def render_final_failure(project_name: str, reason: str, next_action: str) -> str:
    return render_slypilot_message(
        "Analyse impossible.",
        [
            f"Projet : {project_name}",
            "",
            "Raison :",
            reason,
            "",
            "Action suivante :",
            next_action,
        ],
    )
