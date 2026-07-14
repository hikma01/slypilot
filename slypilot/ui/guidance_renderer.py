"""Conversation guidance renderer for SlyPilot."""

from __future__ import annotations

from slypilot.coordinator.expert_interpreter import ExpertDiagnostic, interpret_expert_diagnostic
from slypilot.contracts import safe_project_label

from .chat_renderer import render_slypilot_message


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _section_content(section: object) -> str:
    if isinstance(section, dict):
        return str(section.get("content", "")).strip()
    return str(section or "").strip()


def _bullet_lines(text: str) -> list[str]:
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            lines.append(stripped[2:].strip())
    return lines


def _unique_preserve(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def _is_technology_label(value: str) -> bool:
    lowered = value.lower()
    if lowered.endswith((".yml", ".yaml", ".txt", ".py", ".json", ".md")):
        return False
    if "/" in value or "\\" in value:
        return False
    return True


_PEDAGOGICAL_GLOSSARY: dict[str, str] = {
    "Python": "langage principal du projet",
    "Docker": "environnement isolé permettant d'exécuter le projet",
    "PostgreSQL": "base de données principale",
    "API": "point d'entrée permettant aux systèmes de communiquer",
    "worker": "processus exécutant des tâches en arrière-plan",
    "workers": "processus exécutant des tâches en arrière-plan",
    "docker-compose.yml": "fichier qui décrit comment démarrer les composants du projet",
    "requirements.txt": "liste les bibliothèques Python utilisées",
    "repo-map.md": "carte qui décrit l'organisation du dépôt",
    "runtime-map.md": "carte qui décrit l'environnement d'exécution",
    "dependency-map.md": "carte qui résume les dépendances principales",
    "semantic_index.md": "carte qui regroupe les domaines repérés",
    "interpreted_tree.md": "arborescence pédagogique interprétée",
}


_ACTION_LABELS: dict[str, str] = {
    "show_cartography": "afficher la cartographie",
    "enrich_cartography": "enrichir la cartographie",
    "stop_here": "arrêter ici",
    "analyze_project": "analyser le projet",
    "minimal_project_scan": "analyse minimale immédiate",
    "cancel": "annuler",
    "prepare_project": "initialiser ARCHI OPS",
    "start_analysis": "lancer l'analyse",
    "analyze_files": "analyser les fichiers importants",
    "show_map": "afficher la cartographie",
    "find_risks": "rechercher les zones à risque",
    "info": "expliquer ARCHI OPS",
}


def _pedagogical_label(value: str, seen: set[str]) -> str:
    cleaned = value.strip()
    role = _PEDAGOGICAL_GLOSSARY.get(cleaned)
    if role and cleaned not in seen:
        seen.add(cleaned)
        return f"{cleaned} ({role})"
    seen.add(cleaned)
    return cleaned


def _pedagogical_lines(values: list[str], seen: set[str]) -> list[str]:
    return [f"- {_pedagogical_label(value, seen)}" for value in values]


def _action_label(value: str) -> str:
    cleaned = value.strip()
    return _ACTION_LABELS.get(cleaned, cleaned.replace("_", " "))


def render_greeting_prompt(include_header: bool = True) -> str:
    return render_slypilot_message(
        "SlyPilot",
        [
            "Bonjour. Je peux t'aider à analyser un projet, comprendre un bug ou explorer une architecture.",
            "Indiquez le projet ou le problème à analyser.",
            "",
            "Exemple :",
            "analyse le projet /Users/.../MonProjet",
        ],
        include_header=include_header
    )


def render_archiops_explanation(project_name: str, include_header: bool = True) -> str:
    return render_slypilot_message(
        "SlyPilot",
        [
            "ARCHI OPS est la cartographie technique utilisée par SlyPilot.",
            "",
            "Elle permet de comprendre un projet sans scanner tout le dépôt à chaque demande.",
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
            f"Sans ARCHI OPS, je peux voir le dossier {project_name}, mais je ne dispose pas encore du contexte suffisant pour analyser proprement.",
        ],
        include_header=include_header
    )


def render_init_required_prompt(project_name: str, project_path: str, include_header: bool = True) -> str:
    return render_slypilot_message(
        "SlyPilot",
        [
            "J'ai trouvé le dossier du projet.",
            f"Projet détecté : {project_name}",
            f"Chemin : {project_path}",
            "",
            "Ce projet n'est pas encore préparé pour l'analyse.",
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
            "",
            "Alternatives :",
            "",
            "[1] Recommandé : Initialiser ARCHI OPS puis analyser",
            "[2] Analyse minimale immédiate",
            "[3] Annuler",
            "",
            "[I] Info — expliquer ARCHI OPS",
            "",
            "Réponds : 1, 2 ou 3.",
        ],
        include_header=include_header
    )


def render_init_confirmation(project_name: str, project_path: str, include_header: bool = True) -> str:
    return render_slypilot_message(
        "SlyPilot",
        [
            "Action sélectionnée :",
            f"initialiser ARCHI OPS pour {project_name}.",
            "",
            "Préparation en cours...",
            "",
            "Action à exécuter :",
            f"slypilot init {project_path}",
        ],
        include_header=include_header
    )


def render_cancel_action(include_header: bool = True) -> str:
    return render_slypilot_message(
        "SlyPilot",
        [
            "Action annulée. Aucune analyse ne sera lancée tant qu'ARCHI OPS n'est pas initialisé.",
        ],
        include_header=include_header
    )


def render_info_followup(include_header: bool = True) -> str:
    return render_slypilot_message(
        "SlyPilot",
        [
            "Que veux-tu faire ?",
            "[O] Oui — initialiser ARCHI OPS",
            "[N] Non — annuler",
            "[I] Info — expliquer ARCHI OPS",
        ],
        include_header=include_header
    )


def render_ambiguity_prompt(project_name: str, project_path: str, include_header: bool = True) -> str:
    return render_slypilot_message(
        "SlyPilot",
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
        include_header=include_header
    )


def render_path_missing(path: str, include_header: bool = True) -> str:
    return render_slypilot_message(
        "SlyPilot",
        [
            "Le chemin fourni n'existe pas.",
            "Chemin :",
            path,
            "",
            "Vérifiez le chemin puis réessayez.",
        ],
        include_header=include_header
    )


def render_sensitive_path(path: str, include_header: bool = True) -> str:
    return render_slypilot_message(
        "SlyPilot",
        [
            "Accès refusé.",
            "Ce chemin est protégé par la politique de sécurité.",
            "",
            "Chemin :",
            path,
            "",
            "SlyPilot ne lit pas les dossiers contenant des clés, secrets ou identifiants.",
        ],
        include_header=include_header
    )


def render_execution_stage(stage: str, state: str, reason: str | None = None) -> str:
    from .chat_renderer import render_technical_info
    msg = f"{stage} : {state}"
    if reason:
        msg += f" ({reason})"
    return render_technical_info(msg)


def render_final_diagnostic(project_name: str, lines: list[str]) -> str:
    return render_slypilot_message(
        "SlyPilot",
        [f"Projet : {project_name}", "", *lines],
        include_header=False
    )


def render_analysis_restitution(
    project_name: str,
    packet_metadata: dict[str, object],
    packet_rel_path: str,
    diagnostic: ExpertDiagnostic | dict[str, object] | None = None,
    verbose: bool = False,
    include_header: bool = False,
) -> str:
    selected_files = _as_list(packet_metadata.get("selected_files", []))
    selected_maps = _as_list(packet_metadata.get("selected_maps", []))
    knowledge_contract = packet_metadata.get("knowledge_contract")
    project_memory = packet_metadata.get("project_memory")

    if not verbose:
        interpreted = diagnostic
        if not isinstance(interpreted, ExpertDiagnostic):
            interpreted = interpret_expert_diagnostic(project_name, packet_metadata)
        seen_terms: set[str] = set()
        summary = interpreted.summary or [f"J'ai identifié une cartographie initiale pour {project_name}."]
        understood = interpreted.understood or [
            "Je n'ai pas encore assez d'indices pour décrire le cœur métier avec précision.",
        ]
        meaning = interpreted.meaning or [
            "Les données disponibles décrivent surtout l'infrastructure du projet.",
        ]
        missing = interpreted.missing or [
            "Je n'ai pas encore identifié de modules métier suffisamment parlants.",
        ]
        why = interpreted.why or [
            "La cartographie actuelle reste trop générale pour aller plus loin sans risque.",
        ]
        lines = [
            f"Projet : {project_name}",
            "",
            "Vue d’ensemble :",
            "",
            *[_pedagogical_label(line, seen_terms) if not line.startswith(("J'", "J’")) else line for line in summary],
            "",
            "Fichiers ARCHI OPS utilisés :",
            *(_pedagogical_lines(selected_maps, seen_terms) if selected_maps else ["- aucun fichier ARCHI OPS exploitable"]),
            "",
            "J'ai détecté :",
            *(_pedagogical_lines(interpreted.detected_technologies, seen_terms) if interpreted.detected_technologies else ["- aucune technologie dominante détectée"]),
            *(_pedagogical_lines(interpreted.detected_files, seen_terms) if interpreted.detected_files else []),
            "",
            "Ce que j'ai compris :",
            *(_pedagogical_lines(understood, seen_terms)),
            "",
            "Ce que cela signifie :",
            *(_pedagogical_lines(meaning, seen_terms)),
            "",
            "Ce qui manque encore :",
            *(_pedagogical_lines(missing, seen_terms)),
            "",
            "Ma recommandation :",
            interpreted.recommendation,
            "",
            "Pourquoi :",
            *(_pedagogical_lines(why, seen_terms)),
        ]
        if isinstance(project_memory, dict):
            memory_lines = _memory_lines(project_memory, seen_terms)
            if memory_lines:
                lines.extend(["", "Mémoire projet :", *memory_lines])
        return render_slypilot_message("SlyPilot", lines, include_header=include_header)

    selected_maps = _as_list(packet_metadata.get("selected_maps", []))
    selection_reasons = _as_list(packet_metadata.get("selection_reasons", []))
    negative_context = _as_list(packet_metadata.get("negative_context", []))
    seen_terms: set[str] = set()
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
    if isinstance(project_memory, dict):
        memory_lines = _memory_lines(project_memory, seen_terms)
        if memory_lines:
            knowledge_lines.extend(["", "Mémoire projet", *memory_lines])
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
        ", ".join(_pedagogical_label(item, seen_terms) for item in selected_maps) if selected_maps else "aucune carte sélectionnée",
        "",
        "Vue d’ensemble :",
        f"- project_yaml_loaded: {str(packet_metadata.get('project_yaml_loaded', False)).lower()}",
        f"- project_contract_injected: {str(packet_metadata.get('project_contract_injected', False)).lower()}",
        f"- context_reduction_ratio: {packet_metadata.get('context_reduction_ratio', 'none')}",
        "",
        "Fichiers clés :",
        *(_pedagogical_lines(selected_files, seen_terms) if selected_files else ["- aucun"]),
        "",
        "Dépendances principales :",
        *(_pedagogical_lines(negative_context, seen_terms) if negative_context else ["- aucune dépendance explicite détectée"]),
        "",
        "Risques ou limites visibles :",
        *([
            f"- {item}"
            for item in selection_reasons[:5]
        ] if selection_reasons else ["- aucune limite notable dans le contexte borné"]),
        "",
        "Connaissance utile transportée :",
        *(knowledge_lines if knowledge_lines else ["none"]),
    ]
    return render_slypilot_message("SlyPilot", lines, include_header=include_header)


def _memory_lines(project_memory: dict[str, object], seen_terms: set[str]) -> list[str]:
    lines: list[str] = []
    technologies = _as_list(project_memory.get("technologies", []))
    domains = _as_list(project_memory.get("domains", []))
    loaded_maps = project_memory.get("loaded_maps", {})
    important_files = _as_list(project_memory.get("important_files", []))
    entry_points = _as_list(project_memory.get("entry_points", []))
    previous_findings = _as_list(project_memory.get("previous_findings", []))
    risks = _as_list(project_memory.get("risks", []))
    architecture_summary = str(project_memory.get("architecture_summary", "") or "").strip()
    business_summary = str(project_memory.get("business_summary", "") or "").strip()
    runtime_summary = str(project_memory.get("runtime_summary", "") or "").strip()
    active_recommendation = str(project_memory.get("active_recommendation", "") or "").strip()

    if technologies:
        lines.append("- Technologies mémorisées : " + ", ".join(_pedagogical_label(item, seen_terms) for item in technologies[:8]))
    if domains:
        lines.append("- Domaines mémorisés : " + ", ".join(_pedagogical_label(item, seen_terms) for item in domains[:8]))
    if architecture_summary:
        lines.append(f"- Architecture mémorisée : {architecture_summary}")
    if business_summary:
        lines.append(f"- Métier mémorisé : {business_summary}")
    if runtime_summary:
        lines.append(f"- Runtime mémorisé : {runtime_summary}")
    if isinstance(loaded_maps, dict) and loaded_maps:
        lines.append("- Cartes persistées : " + ", ".join(sorted(str(key) for key in loaded_maps.keys())))
    if important_files:
        lines.append("- Fichiers importants : " + ", ".join(_pedagogical_label(item, seen_terms) for item in important_files[:5]))
    if entry_points:
        lines.append("- Points d'entrée : " + ", ".join(_pedagogical_label(item, seen_terms) for item in entry_points[:5]))
    if previous_findings:
        lines.append("- Constats déjà retenus :")
        lines.extend([f"  - {item}" for item in previous_findings[:5]])
    if risks:
        lines.append("- Risques persistés :")
        lines.extend([f"  - {item}" for item in risks[:5]])
    if active_recommendation:
        lines.append(f"- Recommandation active : {active_recommendation}")
    if project_memory.get("last_analysis_timestamp"):
        lines.append(f"- Dernière analyse : {project_memory.get('last_analysis_timestamp')}")
    return lines


def render_analysis_discovery(project_name: str, task_type: str, include_header: bool = True) -> str:
    if task_type == "debug":
        lines = [
            "J'ai compris que vous souhaitez rechercher ou corriger un bug.",
            "",
            "Pour mieux cibler mon analyse, pouvez-vous m'en dire plus :",
            "- depuis quand le bug apparaît-il ?",
            "- quel est l'impact ?",
            "- quelle est la zone ou le composant concerné ?",
        ]
    else:
        lines = [
            f"J'ai détecté le projet {project_name}.",
            "",
            "Que souhaitez-vous faire exactement ?",
            "- comprendre le projet dans sa globalité",
            "- comprendre le métier",
            "- rechercher un bug",
            "- auditer l'architecture",
            "- préparer un export pour Codex",
        ]
    return render_slypilot_message("SlyPilot", lines, include_header=include_header)


def render_analysis_plan(project_name: str, focus: str, include_header: bool = True) -> str:
    lines = [
        f"J'ai compris que vous souhaitez :",
        f"- {focus}",
        "",
        "Je propose le plan suivant :",
        "1. Cartographie globale",
        "2. Analyse métier",
        "3. Points d'entrée",
        "4. Zones à risque",
        "5. Synthèse technique",
        "",
        "Durée estimée : 2 minutes.",
        "",
        "Je lance l'analyse maintenant.",
    ]
    return render_slypilot_message("SlyPilot", lines, include_header=include_header)

def render_post_diagnostic_files(project_name: str, packet_metadata: dict[str, object], include_header: bool = False) -> str:
    knowledge_contract = packet_metadata.get("knowledge_contract")
    important_files: list[dict[str, object]] = []
    seen_terms: set[str] = set()
    if isinstance(knowledge_contract, dict):
        value = knowledge_contract.get("important_files", [])
        if isinstance(value, list):
            important_files = [item for item in value if isinstance(item, dict)]

    lines = [
        "Action sélectionnée : Analyser les fichiers importants.",
        "",
        "Je vais identifier les fichiers prioritaires à partir de la cartographie.",
        "",
    ]
    if important_files:
        lines.extend(["Fichiers importants détectés :", ""])
        for item in important_files[:5]:
            path = str(item.get("path", "")).strip()
            if path:
                lines.append(f"- {_pedagogical_label(path, seen_terms)}")
        lines.extend(["", "Lecture possible :"])
        for item in important_files[:5]:
            path = str(item.get("path", "")).strip()
            reason = str(item.get("reason", "")).strip()
            if path:
                label = _pedagogical_label(path, seen_terms)
                lines.append(f"- {label} : {reason}" if reason else f"- {label}")
        
        # Logic detection for confidence
        has_business = False
        if isinstance(knowledge_contract, dict):
            biz = _section_content(knowledge_contract.get("business_map", ""))
            if "PRIMARY BUSINESS MODULES" in biz and "- none" not in biz:
                has_business = True

        if has_business:
            limit_lines = [
                "- la lecture couvre le cœur métier identifié.",
                "- une exploration profonde peut révéler des détails de mise en œuvre supplémentaires.",
            ]
        else:
            limit_lines = [
                "- la lecture reste centrée sur les fichiers visibles et ne couvre pas encore tout le métier.",
            ]

        lines.extend(
            [
                "",
                "Limite :",
                *limit_lines,
            ]
        )
    else:
        lines.extend(
            [
                "Aucun fichier métier important n'a encore été identifié.",
                "",
                "Je recommande d'explorer l'arborescence métier.",
                "",
                "Limite :",
                "- la cartographie reste centrée sur les fichiers racine et les composants techniques visibles.",
            ]
        )
    return render_slypilot_message("SlyPilot", lines, include_header=include_header)


def render_post_diagnostic_map(packet_metadata: dict[str, object], include_header: bool = False) -> str:
    knowledge_contract = packet_metadata.get("knowledge_contract")
    selected_maps = _as_list(packet_metadata.get("selected_maps", []))
    repo_map = runtime_map = dependency_map = ""
    source_lines: list[str] = []
    if isinstance(knowledge_contract, dict):
        repo_artifact = knowledge_contract.get("repo_map")
        runtime_artifact = knowledge_contract.get("runtime_map")
        dependency_artifact = knowledge_contract.get("dependency_map")
        semantic_artifact = knowledge_contract.get("semantic_index")
        business_artifact = knowledge_contract.get("business_map")
        interpreted_tree = knowledge_contract.get("interpreted_tree")
        repo_map = _section_content(repo_artifact)
        runtime_map = _section_content(runtime_artifact)
        dependency_map = _section_content(dependency_artifact)
        for artifact, label in [
            (repo_artifact, "carte de structure"),
            (runtime_artifact, "carte runtime"),
            (dependency_artifact, "carte des dépendances"),
            (semantic_artifact, "carte sémantique"),
            (business_artifact, "carte métier"),
            (interpreted_tree, "arborescence interprétée"),
        ]:
            if isinstance(artifact, dict) and artifact.get("path"):
                source_lines.append(f"- {artifact.get('path')} ({label})")
    if not source_lines and selected_maps:
        source_lines.extend(f"- {item}" for item in selected_maps[:5])

    structure = _bullet_lines(repo_map) or _as_list(packet_metadata.get("selected_files", []))
    runtime = _bullet_lines(runtime_map) or ["Python", "Docker"]
    dependencies = _bullet_lines(dependency_map) or ["requirements.txt", "docker-compose.yml"]

    structure_set = {item.strip() for item in structure if item.strip()}
    runtime_set = {item.strip() for item in runtime if item.strip()}
    dependency_set = {item.strip() for item in dependencies if item.strip()}
    seen_terms: set[str] = set()

    simplified_children = sorted(structure_set)[:2]
    architecture_lines = ["Projet"]
    if simplified_children:
        for item in simplified_children:
            architecture_lines.append(f"├── {item}")
    else:
        architecture_lines.append("├── structure non précisée")
    architecture_lines.append("└── Code métier")

    # Logic detection for confidence
    has_business = False
    if isinstance(knowledge_contract, dict):
        biz = _section_content(knowledge_contract.get("business_map", ""))
        if "PRIMARY BUSINESS MODULES" in biz and "- none" not in biz:
            has_business = True
        elif knowledge_contract.get("important_files"):
            has_business = True

    meaning_lines = [
        "- la carte permet de situer rapidement les points d'entrée utiles",
    ]
    if has_business:
        meaning_lines.append("- elle identifie clairement les modules où réside la logique métier")
    else:
        meaning_lines.append("- elle reste encore trop générale pour identifier le métier avec certitude")

    missing_lines = []
    if has_business:
        missing_lines.extend([
            "- exploration détaillée des flux internes",
            "- validation des interactions entre services",
        ])
        recommendation = "approfondir l'analyse des modules identifiés pour valider la logique métier"
    else:
        missing_lines.extend([
            "- cartographie initiale encore incomplète",
            "- aucun fichier métier principal n'a encore été isolé",
            "- Contexte borné : il ne permet pas encore d'affirmer où se trouve le cœur fonctionnel",
        ])
        recommendation = "explorer l'arborescence métier pour trouver les modules principaux et les services"

    lines = [
        "Fichiers ARCHI OPS utilisés :",
        *(source_lines if source_lines else ["- aucun fichier ARCHI OPS exploitable"]),
        "",
        "Ce que je vois :",
        "Structure détectée :",
    ]
    if structure_set:
        lines.extend(_pedagogical_lines(sorted(structure_set)[:5], seen_terms))
    else:
        lines.append("- aucune structure détectée")
    if runtime_set:
        lines.extend([""] + _pedagogical_lines(sorted(runtime_set)[:5], seen_terms))
    if dependency_set:
        lines.extend([""] + _pedagogical_lines(sorted(dependency_set)[:5], seen_terms))
    lines.extend(
        [
            "",
            "Architecture simplifiée :",
            *architecture_lines,
            "",
            "Ce que cela signifie :",
            *meaning_lines,
            "",
            "Pourquoi c'est important :",
            "- ces éléments indiquent comment le projet démarre",
            "- ils aident à repérer où se trouve probablement le métier",
            "- ils servent de base pour relier les points d'entrée aux services critiques",
            "",
            "Ce qui manque encore :",
            *missing_lines,
            "",
            "Ma recommandation :",
            recommendation,
        ]
    )
    return render_slypilot_message("SlyPilot", lines, include_header=include_header)


def render_post_diagnostic_risks(packet_metadata: dict[str, object], include_header: bool = False) -> str:
    knowledge_contract = packet_metadata.get("knowledge_contract")
    selection_reasons = _as_list(packet_metadata.get("selection_reasons", []))
    
    # Logic detection for confidence
    has_business = False
    if isinstance(knowledge_contract, dict):
        biz = _section_content(knowledge_contract.get("business_map", ""))
        if "PRIMARY BUSINESS MODULES" in biz and "- none" not in biz:
            has_business = True
        elif knowledge_contract.get("important_files"):
            has_business = True

    if has_business:
        lines = [
            "Zones à risque visibles :",
            "",
            "- complexité potentielle des modules métier identifiés",
            "- interactions entre services à valider",
            "- besoin d'une exploration profonde pour confirmer les flux de données",
        ]
    else:
        lines = [
            "Zones à risque visibles :",
            "",
            "- cartographie encore initiale",
            "- aucun fichier métier principal identifié",
            "- Contexte borné encore trop court pour conclure sur la zone critique",
        ]

    if selection_reasons:
        lines.extend(["", "Indices observés :"])
        lines.extend(f"- {item}" for item in selection_reasons[:5])
    return render_slypilot_message("SlyPilot", lines, include_header=include_header)


def render_post_diagnostic_stop() -> str:
    return render_slypilot_message(
        "SlyPilot",
        [
            "Analyse arrêtée. Le contexte projet reste disponible.",
            "Le contexte projet reste disponible dans cette session.",
        ],
    )


def render_post_diagnostic_menu() -> str:
    return render_slypilot_message(
        "SlyPilot",
        [
            "Prochaine étape recommandée :",
            "",
            "Je peux maintenant approfondir l'analyse.",
            "",
            "1 — analyser les fichiers importants",
            "2 — afficher la cartographie",
            "3 — rechercher les zones à risque",
            "4 — arrêter ici",
        ],
    )


def render_pending_action_invalid_choice(pending_action: dict[str, object]) -> str:
    options = pending_action.get("options") if isinstance(pending_action, dict) else None
    option_lines: list[str] = []
    if isinstance(options, dict) and options:
        option_lines.extend(["", "Options disponibles :"])
        for key in sorted(options.keys(), key=str):
            option = options.get(key)
            label = ""
            if isinstance(option, dict):
                label = str(option.get("label") or option.get("action") or "").strip()
            if not label:
                label = str(key)
            option_lines.append(f"{key} — {_action_label(label)}")
    return render_slypilot_message(
        "SlyPilot",
        [
            "Je n'ai pas compris ton choix. Veuillez choisir une option valide.",
            *option_lines,
        ],
    )


def render_pending_action_explanation(pending_action: dict[str, object]) -> str:
    project_name = safe_project_label(pending_action)
    options = pending_action.get("options") if isinstance(pending_action, dict) else None
    recommended_option = str(pending_action.get("recommended_option", "")).strip() if isinstance(pending_action, dict) else ""
    choice_lines: list[str] = []
    if isinstance(options, dict) and options:
        selected_key = recommended_option or next(iter(options.keys()))
        selected_option = options.get(selected_key, {})
        label = ""
        if isinstance(selected_option, dict):
            label = str(selected_option.get("label") or selected_option.get("action") or "").strip()
        if not label:
            label = str(selected_key)
        choice_lines.extend(["", "Le choix conseillé est :", f"{selected_key} — {_action_label(label)}"])
    lines = [
        "Je reformule simplement.",
        f"Tu es dans l'étape de décision pour {project_name}.",
        "",
        "Cette étape sert à choisir la suite la plus utile sans perdre le contexte.",
        "Le diagnostic est en mémoire et je suis prêt pour l'étape suivante.",
        *choice_lines,
    ]
    return render_slypilot_message("SlyPilot", lines)


def render_pending_action_greeting(pending_action: dict[str, object]) -> str:
    project_name = safe_project_label(pending_action)
    options = pending_action.get("options") if isinstance(pending_action, dict) else None
    option_lines: list[str] = []
    if isinstance(options, dict) and options:
        option_lines.extend(["", "Options disponibles :"])
        for key in sorted(options.keys(), key=str):
            option = options.get(key)
            label = ""
            if isinstance(option, dict):
                label = str(option.get("label") or option.get("action") or "").strip()
            if not label:
                label = str(key)
            option_lines.append(f"{key} — {_action_label(label)}")
    lines = [
        "Bonjour.",
        "",
        f"Nous sommes toujours sur l'analyse de {project_name}.",
        "Comment souhaitez-vous continuer ?",
        *option_lines,
    ]
    return render_slypilot_message("SlyPilot", lines)


def render_final_failure(project_name: str, reason: str, next_action: str, include_header: bool = True) -> str:
    return render_slypilot_message(
        "SlyPilot",
        [
            "Analyse impossible.",
            f"Projet : {project_name}",
            "",
            "Raison :",
            reason,
            "",
            "Action recommandée :",
            next_action,
        ],
        include_header=include_header
    )


def render_path_error() -> str:
    from .chat_renderer import render_technical_block
    return render_technical_block(
        "Impossible d'interpréter le chemin fourni.",
        [
            "Le chemin semble contenir des espaces non protégés.",
            "",
            "Essayez :",
            'analyse "/Users/.../Mon Projet"',
            "ou",
            "analyse /Users/.../Mon\\ Projet",
        ],
    )
