# Mémoire Technique : Résolution de l'Hémorragie de Contexte ArchiOps

## Contexte
Entre le 09 et le 10 juin 2026, une série de dysfonctionnements critiques a été identifiée dans le moteur ArchiOps de SlyPilot. Le système échouait à identifier le cœur métier des projets (SlyAudit, SlyKey, SlyCRM), rendant les analyses techniques superficielles ou nulles.

Cette note documente la source des problèmes et les "pansements" (patchs) appliqués pour stabiliser le système de manière universelle.

---

### 1. Cécité Heuristique (Détection des fichiers)
- **Problème :** `cartography_service.py` limitait la détection des points d'entrée à une liste trop restreinte (`main.py`, `app.py`).
- **Impact :** Les fichiers comme `backend.py` ou `index.html` étaient ignorés.
- **Solution :** Élargissement de la liste blanche aux motifs fréquents (`backend.py`, `api.py`, `worker.py`, `index.html`, etc.).

### 2. Barrière de Profondeur (Exploration `src/`)
- **Problème :** Le scan ne regardait qu'à la racine du projet.
- **Impact :** Les projets structurés avec un dossier `src/` ou `app/` (comme SlyCRM) paraissaient vides de logique.
- **Solution :** Implémentation d'un "Deep Scan" explorant les répertoires standards à un niveau de profondeur pour trouver les fichiers `.jsx`, `.tsx`, `.py`, etc.

### 3. Amnésie d'Initialisation (Indexation)
- **Problème :** `archiops_init.py` créait les cartes mais ne peuplait pas la liste des `files` dans `index.yaml`.
- **Impact :** Le coordinateur voyait la structure mais ne savait pas quels fichiers charger en priorité.
- **Solution :** Promotion automatique des points d'entrée détectés comme "fichiers importants" avec un poids élevé (90-95) dès l'initialisation.

### 4. Disconnect de Routage (Coordination)
- **Problème :** `coordinator.py` utilisait l'intention `analyze_project` au lieu du `task_type` technique pour charger ArchiOps.
- **Impact :** Le chargeur de contexte filtrait tout car aucune règle ne correspondait à cette intention générique.
- **Solution :** Utilisation systématique de `intent.task_type` (ex: `patch`, `architecture`) pour le chargement du contexte ArchiOps.

### 5. Étouffement du Contexte (Budgets)
- **Problème :** Le profil `standard` limitait le contexte à 500 lignes.
- **Impact :** Les fichiers monolithiques comme `backend.py` (3700+ lignes) étaient rejetés car trop gros.
- **Solution :** Augmentation massive des limites des profils (Minimal: 1000, Standard: 5000, Premium: 15000 lignes).

### 6. Pessimisme de l'Interface (Rendu UI)
- **Problème :** L'interprète technique et les renderers UI avaient des messages pessimistes codés en dur si aucun dossier `/services/` n'était trouvé.
- **Impact :** SlyPilot disait "Métier non identifié" même quand il avait trouvé `backend.py`.
- **Solution :** Dynamisation des messages basés sur la présence de fichiers importants ou de points d'entrée promus.

---

## Conclusion
Le système est passé d'une **architecture de méfiance statique** (filtres rigides) à une **confiance dynamique** (détection de motifs + budgets flexibles). Cette approche garantit que SlyPilot "trouve le cœur" de n'importe quel projet, peu importe sa stack ou sa structure.

**Date :** 10 juin 2026
**Statut :** Stabilisé et Validé.
