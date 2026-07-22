# Coordinator V2

SlyPilot V2 introduces a central coordinator layer.

Responsibilities:
- resolve intent
- resolve project
- check coherence
- select a strategy
- build a bounded task packet
- block ambiguous or unsafe execution

ARCHI OPS remains the project memory.
Task Packet remains the execution contract.
Providers remain execution engines.

For SlyMethod rollout, the coordinator should consume:
- the STI;
- the Execution Plan when one exists;
- the Implementation Coordination Board;
- the Developer Mission Workflow.

The Board should be treated as the short operational prompt for the next action, not as a replacement for task packets.
