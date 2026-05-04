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
import time
from engine.state import GameState, ActionLog, NarrationResult, NarrationEval
from llm.prompts import build_system_prompt, build_user_prompt, build_context_usage
from llm.memory import get_memory_block
from llm.evaluator import evaluate

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
    

def _call_api(prompt: str, system: str, max_retries: int = 3) -> tuple[str, bool]:
    """
    Call the Anthropic API with exponential backoff.
    Returns (raw_output, fallback_used).
    """
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip(), False
        except Exception as e:
            if attempt == max_retries - 1:
                return "", True
            wait = 2 ** attempt  # 1s, 2s, 4s
            time.sleep(wait)
    return "", True


def narrate(
    state: GameState,
    result: ActionLog,
    memory_block: str = "",
) -> tuple[NarrationResult, str, NarrationEval, dict]:
    """
    Returns (NarrationResult, raw_llm_output, NarrationEval, context_usage).
    """
    prompt = build_user_prompt(state, result, memory_block)
    system = build_system_prompt(state.enemy.enemy_type)
    context_usage = build_context_usage(system, prompt)

    raw, fallback_used = _call_api(prompt, system)

    if fallback_used:
        narration_result = _fallback(result)
    else:
        narration_result = _parse(raw, result)
        if narration_result == _fallback(result):
            fallback_used = True

    eval_result = evaluate(narration_result, raw, fallback_used)
    return narration_result, raw, eval_result, context_usage