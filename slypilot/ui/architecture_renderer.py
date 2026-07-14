"""Visual architecture explorer for SlyPilot CLI."""

from __future__ import annotations

from .chat_renderer import render_slypilot_message
from .style import dim


def render_visual_architecture(
    project_name: str,
    packet_metadata: dict[str, object],
    include_header: bool = False
) -> str:
    """Render a spatial and interpreted view of the project architecture."""
    knowledge = packet_metadata.get("knowledge_contract", {})
    interpreted_tree = None
    if isinstance(knowledge, dict):
        it = knowledge.get("interpreted_tree")
        if isinstance(it, dict):
             interpreted_tree = str(it.get("content", "")).strip()

    if interpreted_tree:
        return _render_from_interpreted_tree(project_name, interpreted_tree, include_header)
    
    # Fallback to dynamic identification if interpreted-tree.md is missing
    return _render_dynamic_view(project_name, packet_metadata, include_header)


def _render_from_interpreted_tree(project_name: str, content: str, include_header: bool) -> str:
    """Render the view using the rich interpreted-tree.md source."""
    lines = [f"Projet {project_name}", ""]
    
    # We parse the markdown to extract relevant sections
    sections = _parse_interpreted_tree(content)
    
    # Level 1 & 2: Interpreted Tree
    tree_content = sections.get("INTERPRETED TREE", "")
    if tree_content:
        lines.append("Arborescence interprétée :")
        lines.append(tree_content)
        lines.append("")

    # Business Core
    core = sections.get("PROBABLE BUSINESS CORE", "")
    if core:
        lines.append("Zones métier identifiées :")
        lines.append(core)
        lines.append("")

    # Level 3: Analysis Entry Points (Coordinator advice)
    entry_points = sections.get("ANALYSIS ENTRY POINTS", "")
    if entry_points:
        lines.append("Poursuivre l'analyse (recommandé) :")
        lines.append(entry_points)

    return render_slypilot_message("Vue visuelle du projet :", lines, include_header=include_header)


def _render_dynamic_view(project_name: str, packet_metadata: dict[str, object], include_header: bool) -> str:
    """Fallback dynamic view when interpreted-tree.md is missing, using enriched visual cartography."""
    lines = [
        f"Projet {project_name}",
        "│",
        "├── Infrastructure",
        "│",
        "├── Application",
        "│",
        "├── Métier",
        "│",
        "└── Tests",
        "",
        "Détail des zones :",
        "",
        "Infrastructure",
        "› Rôle : environnement, déploiement et configuration",
        "› Importance : critique pour l'exécution",
        "› Confiance : élevée (détection automatique)",
        "",
        "Application",
        "› Rôle : point d'entrée, API et logique technique",
        "› Importance : majeure pour le flux",
        "› Confiance : moyenne (dépend du framework)",
        "",
        "Métier",
        "› Rôle : règles de gestion et valeur ajoutée",
        "› Importance : cœur du projet",
        "› Confiance : faible (non identifié pour le moment)",
        "",
        "Tests",
        "› Rôle : validation et non-régression",
        "› Importance : garantie de stabilité",
        "› Confiance : variable (selon la couverture)",
        "",
        "Conseil du coordinateur :",
        "Je recommande d'explorer les dossiers métier pour accroître notre niveau de confiance sur le cœur du projet.",
    ]

    return render_slypilot_message("Vue visuelle du projet :", lines, include_header=include_header)


def _parse_interpreted_tree(content: str) -> dict[str, str]:
    """Simple markdown section parser."""
    sections = {}
    current_section = None
    current_lines = []
    
    for line in content.splitlines():
        if line.startswith("## "):
            if current_section:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = line[3:].strip().upper()
            current_lines = []
        elif current_section:
            current_lines.append(line)
            
    if current_section:
        sections[current_section] = "\n".join(current_lines).strip()
        
    return sections


def _identify_pillars(knowledge: object, selected_files: object) -> list[dict[str, str]]:
    """Identify technical and business pillars from project metadata."""
    pillars = []
    files = [str(f).lower() for f in (selected_files if isinstance(selected_files, list) else [])]
    
    # Infrastructure
    if any("docker" in f for f in files):
        pillars.append({"title": "Docker", "desc": "Lance l'environnement"})
    
    # Runtime
    runtime_map = ""
    if isinstance(knowledge, dict):
        rm = knowledge.get("runtime_map")
        if isinstance(rm, dict):
            runtime_map = str(rm.get("content", "")).lower()
        else:
            runtime_map = str(rm or "").lower()
            
    if "python" in runtime_map or any(f.endswith(".py") for f in files):
        pillars.append({"title": "Python", "desc": "Exécute la logique"})
    elif "node" in runtime_map or "javascript" in runtime_map or any(f.endswith(".js") for f in files):
        pillars.append({"title": "Node.js", "desc": "Exécute la logique"})
    else:
        pillars.append({"title": "Runtime", "desc": "Environnement d'exécution"})

    # Dependencies
    if any("requirements.txt" in f for f in files):
        pillars.append({"title": "Requirements", "desc": "Bibliothèques nécessaires"})
    elif any("package.json" in f for f in files):
        pillars.append({"title": "Dependencies", "desc": "Modules nécessaires"})
    else:
        pillars.append({"title": "Dépendances", "desc": "Composants externes"})

    # Business / Métier
    pillars.append({"title": "Métier", "desc": "Non identifié"})

    return pillars
