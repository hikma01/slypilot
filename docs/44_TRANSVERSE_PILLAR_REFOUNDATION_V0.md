# SlyPilot — Refondation du pilier transverse / Baseline V0

**Date :** 2026-11-27 · **Autorisation :** orientation documentaire CC · **Statut :** `DESIGN_CANDIDATE / NOT_ACTIVE / RESET_NOT_EXECUTED`.

## 1. Finalité et frontières

SlyPilot devient le **pilier structurel candidat de coordination de missions entre projets et agents** ; il n'est ni une application métier, ni un second SlyMethod, ni un remplaçant de SlyObserve ou de SlyInfra.

| Composant | Responsabilité propriétaire |
|---|---|
| Humain / CC | Objectifs, périmètre, décisions réservées, ratification |
| **SlyPilot** (cible) | Réception d'un mandat, qualification, routage vers outils spécialisés, coordination des retours, synthèse VSBP |
| **SlyDev** (outil spécialisé) | Développement logiciel, pipeline M01–M06, ses agents et ses résultats d'ingénierie |
| SlyMethod | Méthodes, contrats, rôles, Gates, RETEX et release |
| SlyInfra | Identités, permissions, environnements, Git, CI/CD, rollback |
| SlyObserve | Événements, corrélations et preuves réelles ; `UNKNOWN` si absence |
| SlyPlatform | Core SlyDoc / SlyKnowledge / SlyOrganize, ADR-CORE inchangée |
| Applications métier | Logique métier, parcours utilisateurs et décisions produit |

La nouvelle orientation **ne modifie ni le code SlyDev ni sa route `/admin/slyobserve/slydev`**, et ne renomme pas les décisions historiques G0/G1. La classification UI G2 reste à arbitrer.

## 2. Reset logique sans destruction des preuves

Le dépôt contient une V1 Python, ARCHI OPS, Task Packets, benchmarks et traces historiques. Ils sont **LEGACY / UNQUALIFIED_FOR_NEW_PILLAR** ; on repart d'une **nouvelle baseline conceptuelle**, pas d'une promesse que le runtime ancien fonctionne encore.

**Contrôle initial :** `slypilot/runtime/conversation_loop.py` importe des modules absents de l'arbre Git `main` observé le 2026-11-27 (`session_manager.py`, `session_store.py`, `workflow_engine.py`, `execution_timeline.py` notamment). Les anciens rapports de tests ne prouvent donc pas un PASS actuel.

La séquence de refondation à autoriser séparément :

1. Fig­er le SHA historique et l'inventaire ; préserver l'historique Git, les tests, preuves et benchmarks.
2. Créer une **branche/worktree de refondation isolé** hors synchronisation Nextcloud ; aucune mutation du `main` actif avant QA.
3. Classer chaque composant : `REUSE_AFTER_TEST`, `REWRITE`, `ARCHIVE`, `DISCARD_FROM_NEW_RUNTIME`. Le moteur `coordinator/` et les Task Packets sont candidats d'audit ; les imports de `runtime/` requièrent correction/refonte.
4. Construire un seul flux utile, avec tests réels, négatifs, indépendance QA et rollback démontrés.
5. Promouvoir uniquement sur décision CC après preuves ; maintenir les artefacts historiques disponibles pour RETEX.

**Interdits dans cette phase documentaire :** `git push --force`, suppression d'historique, effacement massif du legacy, migration silencieuse, modification de SlyDev, production ou ouverture de nouvel ARC.

## 3. Première boucle minimale à démontrer

```text
Mission CC autorisée
→ SlyPilot : comprendre le contrat, vérifier les capacités et le DAG
→ SlyDev : exécuter la mission de développement dans son mandat
→ SlyObserve : événements et preuves corrélées réels
→ QA indépendante : PASS / FAIL / UNKNOWN
→ SlyPilot : consolidation, correction bornée ou escalade
→ CC : résultat vérifiable, ratification si requise
```

**Definition of Done V0 :** une mission réelle, un routage, un retour SlyDev authentifié, des identifiants et preuves corrélés, test de refus en absence de permission, aucun faux PASS, zéro aller-retour CC pour des choix techniques ordinaires autorisés. Ni microservices ni orchestration multi-produits tant que ce flux n'est pas prouvé.

## 4. Contrats, méthodes, observabilité

- **Capacités et accès :** `MISSION_CAPABILITY_PLAN@1` proposé par SlyMethod v2.0-rc2, qui reste `NOT_RELEASED`. Ne pas confondre la présence d'un contrat et un grant effectif.
- **Enveloppe de corrélation candidate :** `mission_ref`, `project_id`, `task_id`, `agent_id`, `run_id`, `authority_ref`, `environment`, `contract_version`, `evidence_ref`. Aucun nouveau schéma de production activé par ce texte.
- **État et autorité :** `ROLE != PERMISSION`. Les actions hors mandat, les secrets non disponibles et les preuves absentes restent `BLOCKED / UNKNOWN`, non `PASS`.
- **Propriété :** SlyPilot orchestre **entre** systèmes, SlyDev **dans** les missions de développement. Ne jamais copier un moteur entier : utiliser adaptateurs/contrats versionnés et composants communs testés.

## 5. Gates avant construction

1. Terminer l'arbitrage de classification transverse G2 en gardant G0/G1 historique.
2. Prévol SlyInfra/SlyMethod réellement actives ; confirmer hôtes, outils, accès, identité et droits temporaires disponibles.
3. Figer le périmètre V0, le plan de QA, les tests adversariaux et le contrat de transfert SlyPilot↔SlyDev.
4. Obtenir un mandat d'implémentation distinct et exécuter la première boucle mesurée.
5. À la clôture, Closing Brainstorm + RETEX SlyMethod, sans activation automatique de nouvelles règles.

**Références :** [RFC SlyMethod](https://github.com/hikma01/slymethod/blob/main/04_Architecture/RFC/RFC-SLYMETHOD-SYSTEME-AGENTIQUE-001.md) · [SlyInfra système vivant](https://github.com/hikma01/slyinfra/blob/main/01-FOUNDATION/SYSTEME-VIVANT.md) · [SlyDev issue historique #1](https://github.com/hikma01/slydev/issues/1) · [ADR SlyPlatform Core](https://github.com/hikma01/slyplatform/blob/main/06-DECISIONS/PLATFORM-CORE/ADR-SLYPLATFORM-CORE-001.md).

**VSBP :** état = architecture candidate ; action = audit legacy + G2 ; ensuite = pilote E2E V0 par mandat séparé.
