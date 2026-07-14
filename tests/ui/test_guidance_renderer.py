from __future__ import annotations

from unittest import TestCase

from slypilot.ui import (
    render_ambiguity_prompt,
    render_archiops_explanation,
    render_analysis_restitution,
    render_greeting_prompt,
    render_init_required_prompt,
    render_info_followup,
    render_pending_action_invalid_choice,
    render_pending_action_explanation,
    render_pending_action_greeting,
    render_path_missing,
    render_sensitive_path,
)


class GuidanceRendererTests(TestCase):
    def test_greeting_is_conversational(self) -> None:
        output = render_greeting_prompt()
        self.assertIn("Bonjour.", output)
        self.assertIn("Je peux t'aider", output)

    def test_init_required_explains_why(self) -> None:
        output = render_init_required_prompt("SlyAudit", "/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit")
        self.assertIn("J'ai trouvé le dossier du projet", output)
        self.assertIn("Ma recommandation principale", output)
        self.assertIn("[1] Recommandé", output)
        self.assertIn("[I] Info", output)
        self.assertIn("Réponds :", output)

    def test_archiops_info_explains_concretely(self) -> None:
        output = render_archiops_explanation("SlyAudit")
        self.assertIn("ARCHI OPS est la cartographie technique utilisée par SlyPilot.", output)
        self.assertIn("project.yaml", output)

    def test_ambiguity_prompt_contains_choices(self) -> None:
        output = render_ambiguity_prompt("SlyAudit", "/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit")
        self.assertIn("J'ai détecté une ressource locale", output)
        self.assertIn("Ma recommandation principale", output)
        self.assertIn("1. analyser le projet", output)
        self.assertIn("2. initialiser ARCHI OPS", output)
        self.assertIn("3. afficher l’état du projet", output)

    def test_path_messages_are_human(self) -> None:
        missing = render_path_missing("/Users/hakimradi/Nextcloud/SlyProjet/FakeProject")
        blocked = render_sensitive_path("~/.ssh")
        self.assertIn("Le chemin fourni n'existe pas.", missing)
        self.assertIn("Accès refusé.", blocked)

    def test_info_followup_is_french_only(self) -> None:
        output = render_info_followup()
        self.assertIn("[O] Oui — initialiser ARCHI OPS", output)
        self.assertIn("[N] Non — annuler", output)
        self.assertIn("[I] Info — expliquer ARCHI OPS", output)
        self.assertNotIn("Yes", output)

    def test_pending_action_explanation_is_conversational(self) -> None:
        output = render_pending_action_explanation(
            {
                "project_name": "SlyAudit",
                "recommended_option": "1",
                "options": {
                    "1": {"action": "analyze_project"},
                    "2": {"action": "minimal_project_scan"},
                    "3": {"action": "cancel"},
                },
            }
        )
        self.assertIn("Je reformule simplement.", output)
        self.assertIn("Tu es dans l'étape de décision pour SlyAudit.", output)
        self.assertIn("Le choix conseillé est :", output)
        self.assertIn("1 — analyser le projet", output)
        self.assertNotIn("Yes", output)

    def test_pending_action_invalid_choice_is_french(self) -> None:
        output = render_pending_action_invalid_choice(
            {
                "options": {
                    "1": {"action": "show_cartography"},
                    "2": {"action": "enrich_cartography"},
                    "3": {"action": "stop_here"},
                }
            }
        )
        self.assertIn("Je n'ai pas compris ton choix.", output)
        self.assertIn("1 — afficher la cartographie", output)
        self.assertIn("2 — enrichir la cartographie", output)
        self.assertIn("3 — arrêter ici", output)
        self.assertNotIn("show cartography", output)

    def test_pending_action_greeting_is_conversational(self) -> None:
        output = render_pending_action_greeting(
            {
                "project_name": "SlyAudit",
                "options": {
                    "1": {"action": "show_cartography"},
                    "2": {"action": "enrich_cartography"},
                    "3": {"action": "stop_here"},
                },
            }
        )
        self.assertIn("Bonjour.", output)
        self.assertIn("Nous sommes toujours sur l'analyse de SlyAudit.", output)
        self.assertIn("afficher la cartographie", output)
        self.assertNotIn("show cartography", output)

    def test_analysis_restitution_is_readable(self) -> None:
        output = render_analysis_restitution(
            "SlyAudit",
            {
                "project_yaml_loaded": True,
                "project_contract_injected": True,
                "context_reduction_ratio": 12.5,
                "selected_maps": ["Documents/ARCHIOPS/repo-map.md", "Documents/ARCHIOPS/runtime-map.md"],
                "selected_files": ["src/app.py", "src/service.py"],
                "negative_context": ["- do not scan node_modules"],
                "selection_reasons": ["src/app.py: task_relevance=selected", "src/service.py: task_relevance=selected"],
            },
            "slypilot/packets/generated/task_123.md",
        )
        self.assertIn("Vue d’ensemble", output)
        self.assertIn("Python (langage principal du projet)", output)
        self.assertIn("Ce que j'ai compris", output)
        self.assertIn("Ce que cela signifie", output)
        self.assertIn("Ce qui manque encore", output)
        self.assertIn("Ma recommandation", output)
        self.assertIn("Pourquoi", output)
        self.assertNotIn("Prochaine étape", output)
        self.assertNotIn("project_yaml_loaded", output)
        self.assertNotIn("project_contract_injected", output)
        self.assertNotIn("context_reduction_ratio", output)
        self.assertNotIn("repo_map", output)
        self.assertNotIn("packet", output.lower())

    def test_analysis_restitution_annotates_first_appearance_of_common_terms(self) -> None:
        output = render_analysis_restitution(
            "SlyAudit",
            {
                "project_yaml_loaded": True,
                "project_contract_injected": True,
                "context_reduction_ratio": 12.5,
                "selected_maps": ["Documents/ARCHIOPS/repo-map.md", "Documents/ARCHIOPS/runtime-map.md"],
                "selected_files": ["docker-compose.yml", "requirements.txt"],
                "negative_context": ["- do not scan node_modules"],
                "selection_reasons": ["docker-compose.yml: runtime_configuration", "requirements.txt: python_dependencies"],
                "knowledge_contract": {
                    "repo_map": {
                        "path": "Documents/ARCHIOPS/repo-map.md",
                        "reason": "repo_structure",
                        "content": "# REPO MAP",
                    },
                    "runtime_map": {
                        "path": "Documents/ARCHIOPS/runtime-map.md",
                        "reason": "runtime_detection",
                        "content": "# RUNTIME MAP\n- Python\n- Docker",
                    },
                    "dependency_map": {
                        "path": "Documents/ARCHIOPS/dependency-map.md",
                        "reason": "dependency_surface",
                        "content": "# DEPENDENCY MAP\n- requirements.txt\n- docker-compose.yml",
                    },
                    "semantic_index": {
                        "path": "Documents/ARCHIOPS/semantic-index.md",
                        "reason": "semantic_surface",
                        "content": "# SEMANTIC INDEX\n- api\n- config\n- tests",
                    },
                    "important_files": [
                        {"path": "docker-compose.yml", "reason": "configuration runtime"},
                        {"path": "requirements.txt", "reason": "dépendances Python"},
                    ],
                },
            },
            "slypilot/packets/generated/task_123.md",
        )
        self.assertIn("Python (langage principal du projet)", output)
        self.assertIn("Docker (environnement isolé permettant d'exécuter le projet)", output)
        self.assertIn("docker-compose.yml (fichier qui décrit comment démarrer les composants du projet)", output)
        self.assertIn("requirements.txt (liste les bibliothèques Python utilisées)", output)

    def test_analysis_restitution_debug_retains_details(self) -> None:
        output = render_analysis_restitution(
            "SlyAudit",
            {
                "project_yaml_loaded": True,
                "project_contract_injected": True,
                "context_reduction_ratio": 12.5,
                "selected_maps": ["Documents/ARCHIOPS/repo-map.md", "Documents/ARCHIOPS/runtime-map.md"],
                "selected_files": ["src/app.py", "src/service.py"],
                "negative_context": ["- do not scan node_modules"],
                "selection_reasons": ["src/app.py: task_relevance=selected", "src/service.py: task_relevance=selected"],
                "knowledge_contract": {
                    "repo_map": {
                        "path": "Documents/ARCHIOPS/repo-map.md",
                        "reason": "repo_structure",
                        "content": "# REPO MAP",
                    }
                },
            },
            "slypilot/packets/generated/task_123.md",
            verbose=True,
        )
        self.assertIn("project_yaml_loaded", output)
        self.assertIn("project_contract_injected", output)
        self.assertIn("context_reduction_ratio", output)
        self.assertIn("repo_map", output)

    def test_analysis_restitution_can_surface_project_memory(self) -> None:
        output = render_analysis_restitution(
            "SlyAudit",
            {
                "project_yaml_loaded": True,
                "project_contract_injected": True,
                "context_reduction_ratio": 12.5,
                "selected_maps": ["Documents/ARCHIOPS/repo-map.md"],
                "selected_files": ["docker-compose.yml"],
                "knowledge_contract": {
                    "repo_map": {
                        "path": "Documents/ARCHIOPS/repo-map.md",
                        "reason": "repo_structure",
                        "content": "# REPO MAP",
                    }
                },
                "project_memory": {
                    "project_name": "SlyAudit",
                    "project_path": "/Users/hakimradi/Nextcloud/SlyProjet/SlyAudit",
                    "technologies": ["Python", "Docker"],
                    "domains": ["api", "config"],
                    "architecture_summary": "Structure globale cartographiée.",
                    "business_summary": "Cœur métier en cours d'identification.",
                    "runtime_summary": "Python + Docker.",
                    "risks": ["cartographie encore initiale"],
                    "important_files": ["docker-compose.yml"],
                    "entry_points": ["/api/v1/"],
                    "loaded_maps": {"repo_map": "# REPO MAP", "runtime_map": "# RUNTIME MAP"},
                    "generated_artifacts": ["slypilot/packets/generated/task_123.md"],
                    "previous_findings": ["La cartographie reste à enrichir."],
                    "active_recommendation": "Explorer l'arborescence métier.",
                    "last_analysis_timestamp": "2026-06-05T00:00:00+00:00",
                },
            },
            "slypilot/packets/generated/task_123.md",
        )
        self.assertIn("Mémoire projet", output)
        self.assertIn("Technologies mémorisées", output)
        self.assertIn("Cartes persistées", output)
