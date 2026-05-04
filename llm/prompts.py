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
    """Convert GameState into a concise, LLM-readable summary."""
    p = state.player
    e = state.enemy

    return (
        f"Turn: {state.turn}\n"
        f"Player — {hp_label(p.hp, p.max_hp)} ({p.hp}/{p.max_hp} HP)\n"
        f"Enemy  — {e.name}, {hp_label(e.hp, e.max_hp)} ({e.hp}/{e.max_hp} HP)"
    )


def serialize_result(result: ActionLog, state: GameState) -> str:
    """Convert an ActionLog into a concise, LLM-readable action summary."""
    enemy_name = state.enemy.name

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
# Prompt templates
# ---------------------------------------------------------------------------

def build_system_prompt(enemy_type: str = "goblin") -> str:
    voice = CHARACTER_VOICES.get(enemy_type, CHARACTER_VOICES["goblin"])
    return f"""You are a dungeon master narrator.
Your ONLY job is to translate the action result into vivid prose.

The enemy in this scene is a {enemy_type.replace('_', ' ')}.
Narrate their actions in a {voice['style']} voice.
Vocabulary guidance: {voice['vocabulary']}
Example of correct tone: "{voice['example']}"

STRICT RULES:
- Use ONLY the facts given to you
- Do NOT mention HP numbers
- Do NOT invent enemies, items, or events not in the state
- Do NOT address the player directly
- Length: exactly 2-3 sentences

OUTPUT FORMAT:
Respond with valid JSON only. No markdown, no code fences, no extra text.

{{
  "narration": "2-3 sentence immersive description",
  "tone": one of "tense" | "victorious" | "grim" | "neutral",
  "hit": true or false
}}
"""


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