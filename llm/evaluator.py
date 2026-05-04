"""
dnd_llm · llm/evaluator.py
==========================
Automatic evaluation of LLM narration output.

Checks narration against the constraints defined in the system prompt.
Produces a NarrationEval for every narration call — no human needed.

Checks
------
- hp_mentioned   : did the LLM leak raw HP numbers into prose?
- sentence_count : is the output within the 2-3 sentence constraint?
- format_valid   : did the JSON parse without hitting the fallback?
- fallback_used  : did the LLM fail entirely?
"""

import re
from engine.state import NarrationResult, NarrationEval


def evaluate(
    narration_result: NarrationResult,
    raw_llm_output: str,
    fallback_used: bool,
) -> NarrationEval:
    """
    Evaluate a single narration result against prompt constraints.
    Returns a NarrationEval with pass/fail fields.
    """
    text = narration_result.narration

    return NarrationEval(
        hp_mentioned=_check_hp_mentioned(text),
        sentence_count=_count_sentences(text),
        format_valid=_check_format_valid(raw_llm_output),
        fallback_used=fallback_used,
    )


def _check_hp_mentioned(text: str) -> bool:
    """
    True if the narration mentions a raw HP number pattern.
    Catches patterns like '14 HP', '14hp', 'HP: 14', '14 health points'.
    """
    patterns = [
        r"\d+\s*hp",
        r"hp\s*:?\s*\d+",
        r"\d+\s*health\s*points?",
        r"\d+/\d+",          # catches "14/20" style HP fractions
    ]
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in patterns)


def _count_sentences(text: str) -> int:
    """
    Count sentences by splitting on '.', '!', '?'.
    Strips empty segments to avoid counting trailing punctuation.
    """
    sentences = re.split(r'[.!?]+', text.strip())
    return len([s for s in sentences if s.strip()])


def _check_format_valid(raw: str) -> bool:
    """
    True if the raw LLM output looks like valid JSON.
    Does not re-parse — just checks surface structure.
    """
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return cleaned.startswith("{") and cleaned.endswith("}")