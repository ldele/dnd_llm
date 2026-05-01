"""
dnd_llm · llm/narrator.py
=========================
LLM narration layer. Wraps the Anthropic API and enforces
the constraint that the LLM is a pure narrator — it receives
facts from the engine and returns prose only.

Design rules
------------
- LLM never receives raw state — always serialized via prompts.py
- Memory context injected via memory.py
- LLM never modifies or invents game state
"""

from anthropic import Anthropic
from dotenv import load_dotenv
from engine.state import GameState, ActionLog
from llm.prompts import SYSTEM_PROMPT, build_user_prompt

load_dotenv()
client = Anthropic()


def narrate(
    state: GameState,
    result: ActionLog,
    memory_block: str = "",
) -> str:
    """
    Generate immersive narration for a single action result.
    Accepts optional memory_block for story continuity.
    Returns a 2-3 sentence prose string.
    """
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=150,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": build_user_prompt(state, result, memory_block)},
        ],
    )
    return response.content[0].text.strip()