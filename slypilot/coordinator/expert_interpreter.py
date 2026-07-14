"""Interpret raw coordinator knowledge into a senior-level diagnostic."""

from __future__ import annotations

from dataclasses import dataclass, asdict
import re
from typing import Iterable


_TECH_ALIASES = {
    "python": "Python",
    "py": "Python",
    "docker": "Docker",
    "docker-compose": "Docker",
    "node": "Node.js",
    "nodejs": "Node.js",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "sqlite": "SQLite",
    "redis": "Redis",
    "api": "API",
    "worker": "worker",
    "workers": "workers",
    "service": "service",
    "services": "services",
    "frontend": "frontend",
    "backend": "backend",
    "tests": "tests",
    "docs": "documentation",
    "config": "configuration",
}


_BUSINESS_TERMS = {
    "api",
    "service",
    "services",
    "worker",
    "workers",
    "handler",
    "handlers",
    "domain",
    "domains",
    "feature",
    "features",
    "controller",
    "controllers",
    "route",
    "routes",
    "usecase",
    "usecases",
    "model",
    "models",
    "backend",
    "server",
    "app",
}


@dataclass(frozen=True)
class ExpertDiagnostic:
    project_name: str
    summary: list[str]
    understood: list[str]
    meaning: list[str]
    missing: list[str]
    recommendation: str
    why: list[str]
    next_step: list[str]
    detected_technologies: list[str]
    detected_files: list[str]
    detected_domains: list[str]
    confidence: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def interpret_expert_diagnostic(
    project_name: str,
    packet_metadata: dict[str, object],
    coordinator_context: dict[str, object] | None = None,
) -> ExpertDiagnostic:
    knowledge_contract = packet_metadata.get("knowledge_contract")
    selected_files = _unique_preserve(_flatten_strings(packet_metadata.get("selected_files", [])))
    selected_maps = _unique_preserve(_flatten_strings(packet_metadata.get("selected_maps", [])))
    selection_reasons = _unique_preserve(_flatten_strings(packet_metadata.get("selection_reasons", [])))
    negative_context = _unique_preserve(_flatten_strings(packet_metadata.get("negative_context", [])))

    repo_map = _extract_section_content(knowledge_contract, "repo_map")
    runtime_map = _extract_section_content(knowledge_contract, "runtime_map")
    dependency_map = _extract_section_content(knowledge_contract, "dependency_map")
    semantic_index = _extract_section_content(knowledge_contract, "semantic_index")
    important_files = _extract_important_files(knowledge_contract)

    detected_technologies = _unique_preserve(
        [
            *_detect_technologies(runtime_map),
            *_detect_technologies(dependency_map),
            *_detect_technologies(semantic_index),
            *_detect_technologies(selected_files),
            *_detect_technologies(important_files),
        ]
    )
    detected_domains = _unique_preserve(_extract_domains(semantic_index))
    key_files = _unique_preserve([*important_files, *selected_files])
    business_files = [item for item in key_files if _looks_like_business_file(item)]

    summary = _build_summary(project_name, detected_technologies, key_files, selected_maps)
    understood = _build_understood(detected_technologies, key_files, selected_maps, repo_map, runtime_map)
    meaning = _build_meaning(detected_technologies, detected_domains, selection_reasons, negative_context)
    missing = _build_missing(detected_technologies, detected_domains, business_files, selection_reasons)
    recommendation = _build_recommendation(detected_technologies, detected_domains, business_files)
    why = _build_why(detected_technologies, detected_domains, business_files, negative_context)
    next_step = [
        "1 — analyser les fichiers importants",
        "2 — afficher la cartographie",
        "3 — rechercher les zones à risque",
        "4 — arrêter ici",
    ]

    confidence = "bonne" if detected_technologies or key_files else "moyenne"
    if coordinator_context and str(coordinator_context.get("decision", "")).startswith("block"):
        confidence = "faible"

    return ExpertDiagnostic(
        project_name=project_name,
        summary=summary,
        understood=understood,
        meaning=meaning,
        missing=missing,
        recommendation=recommendation,
        why=why,
        next_step=next_step,
        detected_technologies=detected_technologies,
        detected_files=key_files,
        detected_domains=detected_domains,
        confidence=confidence,
    )


def _extract_section_content(knowledge_contract: object, section_name: str) -> str:
    if not isinstance(knowledge_contract, dict):
        return ""
    section = knowledge_contract.get(section_name)
    if isinstance(section, dict):
        return str(section.get("content", "")).strip()
    return str(section or "").strip()


def _flatten_strings(value: object) -> list[str]:
    if isinstance(value, list):
        flattened: list[str] = []
        for item in value:
            if isinstance(item, dict):
                path = str(item.get("path", "")).strip()
                if path:
                    flattened.append(path)
                content = str(item.get("content", "")).strip()
                if content:
                    flattened.extend([line.strip() for line in content.splitlines() if line.strip()])
                continue
            text = str(item).strip()
            if text:
                flattened.append(text)
        return flattened
    if isinstance(value, str):
        return [line.strip() for line in value.splitlines() if line.strip()]
    return []


def _unique_preserve(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        cleaned = item.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        unique.append(cleaned)
    return unique


def _detect_technologies(texts: object) -> list[str]:
    detected: list[str] = []
    if isinstance(texts, str):
        candidates = [texts]
    else:
        candidates = _flatten_strings(texts)
    for text in candidates:
        lowered = text.lower()
        for needle, label in _TECH_ALIASES.items():
            if needle in lowered and label not in detected:
                detected.append(label)
    return detected


def _extract_domains(content: str) -> list[str]:
    domains: list[str] = []
    for line in content.splitlines():
        cleaned = _clean_line(line)
        if cleaned and cleaned.lower() not in {"semantic index", "detected domains"}:
            domains.append(cleaned)
    return domains


def _extract_important_files(knowledge_contract: object) -> list[str]:
    if not isinstance(knowledge_contract, dict):
        return []
    important_files = knowledge_contract.get("important_files", [])
    result: list[str] = []
    if isinstance(important_files, list):
        for item in important_files:
            if isinstance(item, dict):
                path = str(item.get("path", "")).strip()
                if path:
                    result.append(path)
            else:
                text = str(item).strip()
                if text:
                    result.append(text)
    return result


def _clean_line(line: str) -> str:
    cleaned = re.sub(r"^\s*[-*#>\d\.\)]+\s*", "", line).strip()
    return cleaned


def _looks_like_business_file(path: str) -> bool:
    lowered = path.lower()
    return any(
        marker in lowered
        for marker in (
            "app.",
            "main.",
            "backend",
            "api",
            "server",
            "service",
            "worker",
            "handler",
            "controller",
            "route",
            "domain",
            "feature",
            "model",
            "src/",
            "app/",
            "services/",
            "workers/",
            "routes/",
        )
    )


def _build_summary(
    project_name: str,
    detected_technologies: list[str],
    key_files: list[str],
    selected_maps: list[str],
) -> list[str]:
    summary: list[str] = []
    if detected_technologies:
        techs = ", ".join(detected_technologies[:2])
        summary.append(f"J’ai détecté une base technique centrée sur {techs}.")
    else:
        summary.append("J’ai détecté une cartographie technique initiale, mais les technologies dominantes restent peu explicites.")

    if key_files:
        files = ", ".join(key_files[:2])
        summary.append(f"Les fichiers les plus utiles pour une première lecture sont {files}.")
    elif selected_maps:
        summary.append("Les cartes projet sont bien présentes, mais elles n'ont pas encore permis d'isoler des fichiers métier évidents.")
    else:
        summary.append("La lecture disponible reste très partielle.")
    return summary


def _build_understood(
    detected_technologies: list[str],
    key_files: list[str],
    selected_maps: list[str],
    repo_map: str,
    runtime_map: str,
) -> list[str]:
    understood: list[str] = []
    if detected_technologies:
        understood.append(f"Le projet semble principalement organisé autour de {', '.join(detected_technologies[:3])}.")
    if "Python" in detected_technologies and "Docker" in detected_technologies:
        understood.append("La combinaison Python + Docker indique un projet probablement conteneurisé et reproductible.")
    if key_files:
        understood.append("Les fichiers racine servent surtout à comprendre le socle d'exécution, pas encore le cœur métier.")
    if selected_maps:
        understood.append("La cartographie chargée couvre bien les bases du projet, mais reste orientée structure et runtime.")
    if repo_map:
        understood.append("La carte de structure est disponible pour vérifier l'organisation globale du dépôt.")
    if runtime_map:
        understood.append("La carte runtime aide à comprendre l'environnement d'exécution et les technologies principales.")
    return understood


def _build_meaning(
    detected_technologies: list[str],
    detected_domains: list[str],
    selection_reasons: list[str],
    negative_context: list[str],
) -> list[str]:
    meaning: list[str] = []
    if "Python" in detected_technologies and "Docker" in detected_technologies:
        meaning.append("Le projet ressemble à une application Python empaquetée pour tourner dans un environnement Docker.")
    elif detected_technologies:
        meaning.append(f"Les indices techniques suggèrent un socle centré sur {', '.join(detected_technologies[:2])}.")

    if detected_domains:
        meaning.append(
            f"Les domaines détectés ({', '.join(detected_domains[:4])}) montrent que la cartographie commence à pointer vers les sujets métier."
        )
    else:
        meaning.append("Je ne vois pas encore assez d'indices métiers pour préciser la valeur fonctionnelle du projet.")

    if selection_reasons:
        meaning.append("Les éléments chargés sont surtout sélectionnés pour la structure, le runtime et la surface de dépendances.")
    if negative_context:
        meaning.append("Le contexte borné confirme que SlyPilot doit rester prudent et éviter d'élargir trop tôt son exploration.")
    return meaning


def _build_missing(
    detected_technologies: list[str],
    detected_domains: list[str],
    business_files: list[str],
    selection_reasons: list[str],
) -> list[str]:
    missing: list[str] = []
    if not business_files:
        missing.append("Je n'identifie pas encore le cœur métier principal.")
    if not detected_domains:
        missing.append("Les domaines fonctionnels ne ressortent pas encore clairement de la cartographie.")
    if not any(_BUSINESS_TERMS.intersection(path.lower().replace(".", "/").split("/")) for path in business_files):
        missing.append("Les points d'entrée métier restent à confirmer dans l'arborescence.")
    if selection_reasons and any("initial" in reason.lower() for reason in selection_reasons):
        missing.append("La cartographie est encore initiale et doit être enrichie par des incidents ou des fichiers métier.")
    if detected_technologies and len(detected_technologies) <= 2:
        missing.append("Le socle technique est visible, mais la lecture fonctionnelle reste incomplète.")
    return _unique_preserve(missing)


def _build_recommendation(
    detected_technologies: list[str],
    detected_domains: list[str],
    business_files: list[str],
) -> str:
    if business_files:
        if detected_domains:
            return "Approfondir les fichiers métier déjà repérés pour vérifier comment la logique applicative s'organise."
        return "Explorer les fichiers métier détectés pour relier l'infrastructure aux fonctions concrètes du projet."
    if detected_technologies:
        return "Explorer l'arborescence métier afin d'identifier les modules principaux, les points d'entrée et les services."
    return "Compléter la cartographie du projet avant de tirer une conclusion forte."


def _build_why(
    detected_technologies: list[str],
    detected_domains: list[str],
    business_files: list[str],
    negative_context: list[str],
) -> list[str]:
    why: list[str] = []
    if detected_technologies:
        why.append("Les signaux techniques disponibles décrivent d'abord l'environnement d'exécution.")
    if not business_files:
        why.append("Sans fichiers métier clairs, je ne peux pas encore relier la base technique à la valeur fonctionnelle.")
    if detected_domains:
        why.append("Les domaines repérés peuvent servir de point d'entrée pour une analyse plus ciblée.")
    if negative_context:
        why.append("Le contexte borné impose de garder une analyse courte, fiable et guidée.")
    if not why:
        why.append("La cartographie actuelle reste trop générale pour justifier une conclusion plus ambitieuse.")
    return why
