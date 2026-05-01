"""
dnd_llm · game/loop.py
======================
CLI game loop. Stays alive throughout all phases as a
lightweight debugging tool for the engine and LLM layer.
Do not remove in favour of the Streamlit UI.

Usage
-----
    python main.py
"""

from engine.state import init_state
from engine.combat import player_attack, enemy_attack
from llm.narrator import narrate


def game_loop():
    state = init_state()

    print("\n⚔  Welcome to the Dungeon\n")

    while state.status == "ongoing":
        print(f"\n--- Turn {state.turn} ---")
        print(f"  {state.player.name}: {state.player.hp}/{state.player.max_hp} HP")
        print(f"  {state.enemy.name}: {state.enemy.hp}/{state.enemy.max_hp} HP")

        action = input("\nAction (attack / quit): ").strip().lower()

        if action == "quit":
            break

        if action == "attack":
            result = player_attack(state)
            narration = narrate(state, result)
            print(f"\n  {narration}")

            if state.status != "ongoing":
                break

            result = enemy_attack(state)
            narration = narrate(state, result)
            print(f"\n  {narration}")

        state.turn += 1

    if state.status == "victory":
        print("\n⚔  The enemy falls. Victory.\n")
    elif state.status == "defeat":
        print("\n💀  You have been slain.\n")