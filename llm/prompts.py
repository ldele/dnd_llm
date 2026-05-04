"""
dnd_llm · llm/prompts.py
========================
Single interface between the game engine and the LLM.

Responsibilities
----------------
- Semantic serialization: convert raw GameState into prompt-friendly text
- Prompt templates: system prompt + user prompt builder
- (Phase 3+) JSON output schema

Design rule: the LLM never sees raw numbers alone.
Numbers are always accompanied by a semantic label.
"""

from engine.state import GameState, ActionLog
from llm.prompt_registry import get_prompt, ACTIVE_VERSION


# ---------------------------------------------------------------------------
# Semantic helpers
# ---------------------------------------------------------------------------

def hp_label(hp: int, max_hp: int) -> str:
    """Convert raw HP into a narrative condition label."""
    ratio = hp / max_hp
    if ratio <= 0:
        return "dead"
    elif ratio <= 0.25:
        return "critically wounded"
    elif ratio <= 0.5:
        return "bloodied"
    elif ratio <= 0.75:
        return "injured"
    else:
        return "fresh"


def roll_label(roll: int) -> str:
    """Describe the quality of a d20 roll."""
    if roll == 20:
        return "critical hit"
    elif roll >= 15:
        return "solid hit"
    elif roll >= 10:
        return "hit"
    else:
        return "miss"


# ---------------------------------------------------------------------------
# State serializer
# ---------------------------------------------------------------------------

def serialize_state(state: GameState) -> str:
    p = state.player
    enemy_lines = "\n".join(
        f"  - {e.name}: {hp_label(e.hp, e.max_hp)} ({max(e.hp,0)}/{e.max_hp} HP)"
        for e in state.enemies
    )
    return (
        f"Turn: {state.turn}\n"
        f"Player — {hp_label(p.hp, p.max_hp)} ({p.hp}/{p.max_hp} HP)\n"
        f"Enemies:\n{enemy_lines}"
    )


def serialize_result(result: ActionLog, state: GameState) -> str:
    enemy_name = next(
        (e.name for e in state.enemies if e.hp > 0),
        state.enemies[0].name  # fallback to first if all dead
    )

    if result.action == "defend":
        return f"Player braces for impact — defending this turn."

    if result.action == "flee_success":
        return f"Player flees successfully (roll: {result.roll}) — escapes the fight."

    if result.action == "flee_fail":
        return (
            f"Player attempts to flee but fails (roll: {result.roll}) — "
            f"caught by {enemy_name} and takes a free hit."
        )

    # Original attack logic
    if result.actor == "player":
        if result.damage > 0:
            return (
                f"Player attacks {enemy_name} — {roll_label(result.roll)} "
                f"(roll: {result.roll}), deals {result.damage} damage."
            )
        else:
            return f"Player attacks {enemy_name} — miss (roll: {result.roll}), no damage."
    else:
        if result.damage > 0:
            return (
                f"{enemy_name} strikes back — {roll_label(result.roll)} "
                f"(roll: {result.roll}), deals {result.damage} damage."
            )
        else:
            return f"{enemy_name} attacks — miss (roll: {result.roll}), no damage."

# ---------------------------------------------------------------------------
# Character Voices
# ---------------------------------------------------------------------------

CHARACTER_VOICES = {
    "goblin": {
        "style": "chaotic and crude",
        "vocabulary": "short sentences, animalistic energy, desperation",
        "example": "The goblin shrieks and lunges, all tooth and claw and fury.",
    },
    "orc_warrior": {
        "style": "brutal and proud",
        "vocabulary": "heavy, deliberate, honour-focused",
        "example": "The orc advances without flinching, each blow a statement of dominance.",
    },
    "skeleton": {
        "style": "cold and mechanical",
        "vocabulary": "no emotion, clinical, ancient",
        "example": "The skeleton moves with hollow precision, indifferent to pain or fear.",
    },
    "dragon": {
        "style": "ancient and contemptuous",
        "vocabulary": "grand, slow, condescending — this is beneath it",
        "example": "The dragon exhales with mild irritation, as if swatting a fly.",
    },
}

# ---------------------------------------------------------------------------
# Prompts - templates in prompt_registry.py
# ---------------------------------------------------------------------------

def build_system_prompt(
    enemy_type: str = "goblin",
    version: str = ACTIVE_VERSION,
) -> str:
    """
    Build the system prompt for a given enemy type and prompt version.
    Voice profile is injected only for versions that support it (v1.1+).
    """
    prompt_entry = get_prompt(version)
    template = prompt_entry["system"]

    # v1.0 has no voice placeholders — return as-is
    if "{enemy_type}" not in template:
        return template

    voice = CHARACTER_VOICES.get(enemy_type, CHARACTER_VOICES["goblin"])
    return template.format(
        enemy_type=enemy_type.replace("_", " "),
        style=voice["style"],
        vocabulary=voice["vocabulary"],
        example=voice["example"],
    )


def build_user_prompt(
    state: GameState,
    result: ActionLog,
    memory_block: str = "",
) -> str:
    """Assemble the full user-turn prompt from state, action result, and memory."""
    parts = []

    if memory_block:
        parts.append(f"Context:\n{memory_block}")

    parts.append(f"Game state:\n{serialize_state(state)}")
    parts.append(f"Action result:\n{serialize_result(result, state)}")

    return "\n\n".join(parts)

# ---------------------------------------------------------------------------
# Token budget
# ---------------------------------------------------------------------------

CONTEXT_LIMIT = 4096  # claude-haiku context window (conservative estimate)


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 characters per token."""
    return len(text) // 4


def build_context_usage(system: str, user_prompt: str) -> dict:
    """
    Estimate token usage for a narration call.
    Returns a dict for display in the debug panel.
    """
    system_tokens = estimate_tokens(system)
    prompt_tokens = estimate_tokens(user_prompt)
    total = system_tokens + prompt_tokens

    return {
        "system_tokens": system_tokens,
        "prompt_tokens": prompt_tokens,
        "total_tokens": total,
        "context_limit": CONTEXT_LIMIT,
        "budget_used_pct": round(total / CONTEXT_LIMIT * 100, 1),
    }