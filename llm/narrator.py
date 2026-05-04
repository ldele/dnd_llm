"""
dnd_llm · llm/narrator.py
=========================
LLM narration layer. Returns a validated NarrationResult object.
Falls back to a safe default if the LLM output is invalid JSON.

Design rules
------------
- LLM never receives raw state — always serialized via prompts.py
- LLM output is always validated before use
- Caller always receives a NarrationResult, never raw text
"""

import json
from anthropic import Anthropic
from dotenv import load_dotenv
from engine.state import GameState, ActionLog, NarrationResult
from llm.prompts import build_system_prompt, build_user_prompt
from llm.memory import get_memory_block

load_dotenv()
client = Anthropic()


def _fallback(result: ActionLog) -> NarrationResult:
    """Safe default when LLM output cannot be parsed."""
    if result.damage > 0:
        return NarrationResult(
            narration=f"The {result.actor} strikes, dealing {result.damage} damage.",
            tone="tense",
            hit=True,
        )
    return NarrationResult(
        narration=f"The {result.actor} swings and misses.",
        tone="neutral",
        hit=False,
    )


def _parse(raw: str, result: ActionLog) -> NarrationResult:
    """Parse and validate LLM JSON output. Returns fallback on any error."""
    try:
        # Strip accidental markdown fences if model misbehaves
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(cleaned)
        return NarrationResult(**data)
    except Exception:
        return _fallback(result)


def narrate(
    state: GameState,
    result: ActionLog,
    memory_block: str = "",
) -> tuple[NarrationResult, str]:
    """
    Returns (NarrationResult, raw_llm_output).
    Always returns a valid NarrationResult — never raises.
    raw_llm_output is the exact string the LLM produced.
    """
    prompt = build_user_prompt(state, result, memory_block)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=build_system_prompt(state.enemy.enemy_type),
        messages=[
            {"role": "user", "content": prompt},
        ],
    )
    raw = response.content[0].text.strip()
    return _parse(raw, result), raw