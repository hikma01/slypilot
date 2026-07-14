# STI Architectural Integrity Audit

## Objet

Diagnostic et correction du crash `ModuleNotFoundError: No module named 'slypilot.coordinator.contracts'` apparu apres le deplacement de `technical_brief_builder.py` dans `slypilot/coordinator/`.

## Symptome

`slypilot/coordinator/technical_brief_builder.py` utilisait un import relatif:

```python
from .contracts import TechnicalRequestBrief, ProjectBrief
```

Apres deplacement du fichier dans la couche Coordination Technique, cet import cherchait `slypilot.coordinator.contracts`, qui n'existait pas.

## Decision structurelle

Les contrats d'interface ne doivent pas vivre dans `slypilot/cognitive/`.

Raison:

- la couche cognitive consomme les contrats pour qualifier et traduire;
- la couche technique consomme les memes contrats pour executer et repondre;
- placer ces contrats dans `cognitive` force la couche technique a dependre de la couche cognitive;
- cette dependance inverse brouille la separation STI.

Emplacement retenu:

```txt
slypilot/contracts/
```

Role:

```txt
contrats partages Cognitive <-> Coordination Technique
```

Compatibilite:

```txt
slypilot/cognitive/contracts.py
```

reste un shim de re-export vers `slypilot.contracts` pour ne pas casser les imports historiques.

## Emplacements valides

| Fichier | Role | Statut |
| --- | --- | --- |
| `slypilot/contracts/__init__.py` | Contrats partages STI | Source canonique |
| `slypilot/cognitive/contracts.py` | Compatibilite anciens imports | Re-export uniquement |
| `slypilot/coordinator/technical_brief_builder.py` | Construction de `TechnicalRequestBrief` | Couche technique |
| `slypilot/cognitive/cognitive_interface.py` | Qualification conversationnelle | Couche cognitive |
| `slypilot/coordinator/coordinator.py` | Execution technique | Couche technique |

## Matrice de dependances

```txt
slypilot.cognitive.cognitive_interface
  -> slypilot.contracts
  -> slypilot.coordinator.technical_brief_builder

slypilot.coordinator.technical_brief_builder
  -> slypilot.contracts

slypilot.coordinator.coordinator
  -> slypilot.contracts
  -> resource_resolver / project_resolver / archi_ops_loader / task_packet_builder

slypilot.runtime.conversation_loop
  -> slypilot.contracts
  -> slypilot.cognitive.cognitive_interface
  -> slypilot.coordinator.coordinator

slypilot.cognitive.contracts
  -> slypilot.contracts
```

Il n'y a plus de dependance technique directe vers `slypilot.cognitive.contracts`.

## Verification d'etancheite

### Technical Coordinator

Constat:

- ne contient pas de logique de salutation utilisateur de type `Bonjour`;
- ne rend pas de blocs UI conversationnels;
- reste responsable de la resolution technique, des ressources, de la coherence et du paquet de reponse.

Point de vigilance:

- les messages d'erreur contractuels restent techniques en interne, mais sont attrapes par le runtime avant affichage utilisateur.

### Cognitive Interface

Constat:

- ne lit pas directement le filesystem;
- ne lance pas `detect_paths`;
- ne lance pas `resolve_resources`;
- demande au builder technique de construire le brief quand une demande technique est identifiee.

Point de vigilance:

- `CognitiveInterface._signal_technical_request()` appelle `build_technical_brief()`. C'est acceptable dans l'etat actuel car le builder appartient a la couche technique et ne lit pas le disque.

## Correction appliquee

- creation de `slypilot/contracts/__init__.py`;
- remplacement de l'import relatif casse dans `technical_brief_builder.py`;
- migration des imports techniques/runtime vers `slypilot.contracts`;
- maintien de `slypilot/cognitive/contracts.py` comme compatibilite;
- ajout d'un test de non-regression sur le builder deplace et l'erreur contractuelle propre.

## Regle anti-recurrence

Tout contrat partage entre Cognitive et Coordination Technique doit etre importe depuis `slypilot.contracts`.

Interdit:

```txt
coordinator -> cognitive.contracts
```

Autorise:

```txt
cognitive -> contracts
coordinator -> contracts
runtime -> contracts
```
