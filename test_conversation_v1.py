"""Manual conversational test for STI V1 stabilization."""

import os
from pathlib import Path
from slypilot.runtime.conversation_loop import ConversationLoop

def run_test():
    root = Path("/Users/hakimradi/Nextcloud/SlyProjet/SlyPilot")
    # Use the current project itself as a test target
    project_path = "/Users/hakimradi/Nextcloud/SlyProjet/SlyPilot"
    
    inputs = iter([
        "bonjour",
        f"analyse {project_path}",
        "ok",
        "exit"
    ])
    
    def fake_input(prompt):
        try:
            val = next(inputs)
            print(f"👤 Vous > {val}")
            return val
        except StopIteration:
            return "exit"

    loop = ConversationLoop(
        repository_root=root,
        cwd=Path.cwd(),
        input_func=fake_input,
        output_func=print,
        verbose=False # Set to True to see STI audits
    )
    
    print("=== DÉMARRAGE DU TEST CONVERSATIONNEL SLYPILOT ===")
    loop.run()
    print("=== FIN DU TEST ===")

if __name__ == "__main__":
    run_test()
