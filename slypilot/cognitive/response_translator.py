"""Helper to translate technical packets into human language for STI 2."""

from __future__ import annotations
from slypilot.contracts import TechnicalResponsePacket


_DISPLAY_GLOSSARY = {
    "Python": "Python (langage principal du projet)",
    "Docker": "Docker (environnement isolé permettant d'exécuter le projet)",
    "PostgreSQL": "PostgreSQL (base de données principale)",
    "API": "API (point d'entrée permettant aux systèmes de communiquer)",
    "worker": "worker (processus exécutant des tâches en arrière-plan)",
    "workers": "workers (processus exécutant des tâches en arrière-plan)",
    "docker-compose.yml": "docker-compose.yml (fichier qui décrit comment démarrer les composants du projet)",
    "requirements.txt": "requirements.txt (liste les bibliothèques Python utilisées)",
}


def translate_technical_response(packet: TechnicalResponsePacket) -> str:
    """Translate technical findings into pedagogical human language for STI 2."""
    if not packet.validate():
        return (
            "L’analyse technique a été lancée, mais le packet retourné est incomplet.\n\n"
            f"Données reçues :\n"
            f"- projet : {packet.project_name or 'Inconnu'}\n"
            f"- chemin : {'OK' if packet.project_path else 'Absent'}\n"
            "- stack détectée : non\n"
            "- cartographie ArchiOps : absente\n"
            "- risques : non générés\n\n"
            "Point bloquant probable : ArchiOps ne retourne pas encore de TechnicalResponsePacket exploitable."
        )

    if packet.status == "failed":
        errors = ", ".join(packet.errors) if packet.errors else "Erreur inconnue"
        return f"Je n'ai pas pu mener l'analyse à bien. Raison : {errors}. Je vous conseille de vérifier l'accès au projet."
        
    runtime = ", ".join(_display_term(item) for item in packet.technologies)
    
    # 1. Ce que j'ai compris
    msg = "### 1. Ce que j’ai compris\n"
    msg += f"Le projet **{packet.project_name}** est une application basée sur **{runtime or 'une stack non identifiée'}**.\n"
    if not packet.stack_detected:
        msg += "⚠️ La stack technique n'a pas été détectée avec certitude, ce qui limite la précision du diagnostic.\n"
    msg += "\n"

    # 2. Ce que j'ai identifié
    msg += "### 2. Ce que j’ai identifié\n"
    msg += f"**Architecture** : {packet.architecture_summary}\n\n"
    msg += f"**Métier** : {packet.business_summary}\n"
    if packet.generated_files:
        msg += f"\nFichiers cartographiés : {', '.join(_display_term(item) for item in packet.generated_files)}\n"
    msg += "\n"

    # 3. Ce qui reste incertain
    msg += "### 3. Ce qui reste incertain\n"
    if packet.risks:
        msg += "\n".join([f"- {r}" for m in packet.risks for r in m.splitlines() if r.strip()])
    else:
        msg += "La cartographie technique est stable, mais la profondeur métier demande une validation manuelle."
    msg += "\n\n"

    # 4. Ma recommandation
    msg += "### 4. Ma recommandation\n"
    msg += f"{packet.recommendation}\n\n"

    # 5. Prochaine action proposée
    msg += "### 5. Prochaine action proposée\n"
    if not packet.generated_files:
        msg += "Je suggère d'enrichir la cartographie ArchiOps pour obtenir une vue métier plus précise."
    else:
        msg += "Je suggère d'explorer les domaines identifiés pour valider les interactions entre composants."

    project_memory = packet.metadata.get("project_memory") if isinstance(packet.metadata, dict) else None
    if isinstance(project_memory, dict):
        msg += "\n### 6. Mémoire projet\n"
        memory_technologies = _flatten_display_list(project_memory.get("technologies", []))
        memory_domains = _flatten_display_list(project_memory.get("domains", []))
        memory_findings = _flatten_display_list(project_memory.get("previous_findings", []))
        memory_risks = _flatten_display_list(project_memory.get("risks", []))
        loaded_maps = project_memory.get("loaded_maps", {})
        memory_lines: list[str] = []
        if memory_technologies:
            memory_lines.append(f"- Technologies mémorisées : {', '.join(memory_technologies[:8])}")
        if memory_domains:
            memory_lines.append(f"- Domaines mémorisés : {', '.join(memory_domains[:8])}")
        if isinstance(loaded_maps, dict) and loaded_maps:
            memory_lines.append("- Cartes persistées : " + ", ".join(sorted(loaded_maps.keys())))
        if memory_findings:
            memory_lines.append("- Constats déjà retenus :")
            memory_lines.extend([f"  - {item}" for item in memory_findings[:5]])
        if memory_risks:
            memory_lines.append("- Risques persistés :")
            memory_lines.extend([f"  - {item}" for item in memory_risks[:5]])
        active_recommendation = str(project_memory.get("active_recommendation", "") or "").strip()
        if active_recommendation:
            memory_lines.append(f"- Recommandation active : {active_recommendation}")
        if project_memory.get("last_analysis_timestamp"):
            memory_lines.append(f"- Dernière analyse : {project_memory.get('last_analysis_timestamp')}")
        if not memory_lines:
            memory_lines.append("- Mémoire projet disponible, mais sans éléments enrichis exploitables pour l'instant.")
        msg += "\n".join(memory_lines) + "\n"
    
    return msg


def _flatten_display_list(values: object) -> list[str]:
    if isinstance(values, list):
        return [str(item).strip() for item in values if str(item).strip()]
    if isinstance(values, tuple):
        return [str(item).strip() for item in values if str(item).strip()]
    if values is None:
        return []
    cleaned = str(values).strip()
    return [cleaned] if cleaned else []


def _display_term(value: str) -> str:
    cleaned = value.strip()
    return _DISPLAY_GLOSSARY.get(cleaned, cleaned)
