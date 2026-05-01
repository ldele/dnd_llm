"""
dnd_llm · main.py
=================
Entry point for the LLM Dungeon & Dragon game.

Launches the CLI game loop (Phase 1 baseline).
The Streamlit UI (Phase 4) will replace this as the primary interface,
but this file stays alive as a debugging tool for the engine.

Usage
-----
    python main.py

Architecture
------------
    main.py → game/loop.py → engine/ (combat, state)
                           → llm/    (narration, phase 3+)
"""
from game.loop import game_loop

if __name__ == "__main__":
    game_loop()