"""
dnd_llm · llm/narrator.py
=========================
LLM narration layer. Wraps the OpenAI API and enforces
the constraint that the LLM is a pure narrator — it receives
facts from the engine and returns prose only.

Design rules
------------
- LLM never receives raw state — always serialized via prompts.py
- LLM never returns structured data at this phase (Phase 5+ upgrade)
- Caller always passes both state AND result — never one without the other
"""

from openai import OpenAI
from engine.state import GameState, ActionLog
from llm.prompts import SYSTEM_PROMPT, build_user_prompt

client = OpenAI()


def narrate(state: GameState, result: ActionLog) -> str:
    """
    Generate immersive narration for a single action result.
    Returns a 2-3 sentence prose string.
    """
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        max_tokens=150,
        temperature=0.8,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(state, result)},
        ],
    )
    return response.choices[0].message.content.strip()