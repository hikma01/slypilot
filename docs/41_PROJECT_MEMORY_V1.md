# Architecture de Mémoire Projet — V1 (Concept)

## 1. Vision
L'objectif de la **Project Memory** est de transformer SlyPilot d'un outil d'analyse ponctuel en un coordinateur technique capable d'apprendre son environnement. Le système doit pouvoir mémoriser un projet dès son premier contact (via un chemin absolu) pour permettre des interactions ultérieures simplifiées via des noms ou des alias.

## 2. Schéma Conceptuel (Project Registry)

La mémorisation s'appuiera sur un registre centralisé (`project_registry`) structuré comme suit :

| Champ | Type | Description |
| :--- | :--- | :--- |
| `project_id` | UUID | Identifiant unique interne. |
| `project_name` | String | Nom canonique extrait (ex: `SlyAudit`). |
| `project_path` | String | Chemin local absolu vérifié. |
| `aliases` | List[String] | Variantes de nom repérées dans le texte (ex: `audit`, `sly-audit`). |
| `first_seen_at` | Timestamp | Date de la première détection. |
| `last_seen_at` | Timestamp | Date de la dernière utilisation réussie. |
| `usage_count` | Integer | Nombre de fois où le projet a été sollicité. |

## 3. Flux de Résolution Futur (Cible)

### Phase A : Apprentissage (Premier contact)
1. L'utilisateur saisit : `analyse /Users/hakim/Projets/SlyAudit`.
2. Le `ResourceResolver` valide l'existence du chemin.
3. Le coordinateur vérifie si ce chemin est déjà connu dans le registre.
4. Si inconnu, une entrée est créée avec le nom `SlyAudit`.

### Phase B : Reconnaissance (Contacts suivants)
1. L'utilisateur saisit : `analyse slyaudit`.
2. Le `ProjectResolver` interroge le registre par `project_name` ou `aliases`.
3. Correspondance trouvée → Le chemin `/Users/hakim/Projets/SlyAudit` est automatiquement injecté dans le contexte.
4. L'analyse démarre sans demander de précision géographique.

## 4. Impacts sur le Resolver V2
L'introduction de la mémoire projet aura les impacts suivants :
- **Priorité de Résolution** : Le registre devient la source de vérité prioritaire devant les règles statiques (`projects.yaml`).
- **Désambiguïsation** : Si deux chemins différents portent le même nom, le système utilisera `last_seen_at` pour proposer le projet le plus récent.
- **Auto-Correction** : Le système pourra suggérer d'enregistrer un nouvel alias s'il détecte une variation récurrente dans les messages utilisateur.

## 5. Contraintes de Conception
- **Déterminisme** : Le registre doit rester explicable. L'utilisateur doit pouvoir lister ce que SlyPilot "sait" via une commande `projects list`.
- **Indépendance** : Le registre est découplé de la session de conversation ; il survit à la fermeture du programme.

---
*Document de conception généré le 1er juin 2026 par Gemini CLI.*
