"""
dnd_llm · llm/memory.py
========================
Conversation memory via rolling summarization.

Strategy
--------
- Keep last N turns in full (RECENT_TURNS_LIMIT)
- Summarize everything older into a single paragraph
- Inject summary into every narration prompt
- Summary is regenerated every SUMMARY_EVERY_N turns

This keeps context size bounded regardless of session length.
"""

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

RECENT_TURNS_LIMIT = 3      # turns kept in full
SUMMARY_EVERY_N = 3         # regenerate summary every N turns


SUMMARY_SYSTEM_PROMPT = """You are a dungeon master keeping a record of a battle.
Summarize the combat so far in 2-3 sentences, past tense.
Be concise. Focus on key moments — hits, misses, turning points.
Do NOT invent events. Only summarize what is given to you.
"""


def summarize(log_entries: list[str]) -> str:
    """Compress a list of narration strings into a short summary paragraph."""
    if not log_entries:
        return ""

    combined = "\n".join(f"- {entry}" for entry in log_entries)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=150,
        system=SUMMARY_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Narration log:\n{combined}\n\nSummarize this."}
        ],
    )
    return response.content[0].text.strip()


def get_memory_block(
    log: list[str],
    current_summary: str,
    turn: int,
) -> tuple[str, str]:
    """
    Returns (memory_block, updated_summary).

    memory_block  — string to inject into the narration prompt
    updated_summary — new summary if regenerated, else current_summary
    """
    updated_summary = current_summary

    # Regenerate summary on schedule
    if turn > RECENT_TURNS_LIMIT and turn % SUMMARY_EVERY_N == 0:
        older = log[:-RECENT_TURNS_LIMIT] if len(log) > RECENT_TURNS_LIMIT else []
        if older:
            updated_summary = summarize(older)

    # Build memory block
    parts = []
    if updated_summary:
        parts.append(f"Story so far:\n{updated_summary}")

    recent = log[-RECENT_TURNS_LIMIT:]
    if recent:
        recent_text = "\n".join(f"- {entry}" for entry in recent)
        parts.append(f"Recent turns:\n{recent_text}")

    memory_block = "\n\n".join(parts)
    return memory_block, updated_summary