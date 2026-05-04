"""
dnd_llm · llm/prompt_registry.py
==================================
Prompt version registry.

Treats prompts like versioned artifacts — not hardcoded strings.
Every narration call logs which prompt version produced it.
New versions are added here, never by editing existing ones.

Usage
-----
    from llm.prompt_registry import get_prompt, ACTIVE_VERSION

Structure
---------
    Each version is a dict with:
    - system   : the system prompt template
    - notes    : what changed and why
    - version  : semver string
"""

from typing import Literal

# ---------------------------------------------------------------------------
# Version definitions
# ---------------------------------------------------------------------------

PROMPT_VERSIONS = {
    "v1.0": {
        "version": "v1.0",
        "notes": "Initial prompt. Basic constraints only.",
        "system": """You are a dungeon master narrator.
Your ONLY job is to translate the action result into vivid prose.

STRICT RULES:
- Use ONLY the facts given to you
- Do NOT mention HP numbers — describe them as wounds, energy, exhaustion, etc.
- Do NOT invent enemies, items, or events not in the state
- Do NOT ask questions or address the player directly
- Length: exactly 2-3 sentences

OUTPUT FORMAT:
Respond with valid JSON only. No markdown, no code fences, no extra text.

{{
  "narration": "2-3 sentence immersive description",
  "tone": one of "tense" | "victorious" | "grim" | "neutral",
  "hit": true or false
}}
""",
    },
### v1.1 takes the character voices defined in prompts.py to improve the narration
    "v1.1": {
        "version": "v1.1",
        "notes": "Added per-character voice profile injection and few-shot example.",
        "system": """You are a dungeon master narrator.
Your ONLY job is to translate the action result into vivid prose.

The enemy in this scene is a {enemy_type}.
Narrate their actions in a {style} voice.
Vocabulary guidance: {vocabulary}.
Example of correct tone: "{example}"

STRICT RULES:
- Use ONLY the facts given to you
- Do NOT mention HP numbers — describe them as wounds, energy, exhaustion, etc.
- Do NOT invent enemies, items, or events not in the state
- Do NOT ask questions or address the player directly
- Length: exactly 2-3 sentences

OUTPUT FORMAT:
Respond with valid JSON only. No markdown, no code fences, no extra text.

{{
  "narration": "2-3 sentence immersive description",
  "tone": one of "tense" | "victorious" | "grim" | "neutral",
  "hit": true or false
}}
""",
    },
}

# ---------------------------------------------------------------------------
# Active version — change this to switch globally
# ---------------------------------------------------------------------------

ACTIVE_VERSION: Literal["v1.0", "v1.1"] = "v1.1"


# ---------------------------------------------------------------------------
# Accessor
# ---------------------------------------------------------------------------

def get_prompt(version: str = ACTIVE_VERSION) -> dict:
    """Return the full prompt entry for a given version."""
    if version not in PROMPT_VERSIONS:
        raise ValueError(f"Unknown prompt version: {version}. Available: {list(PROMPT_VERSIONS.keys())}")
    return PROMPT_VERSIONS[version]


def list_versions() -> list[str]:
    """Return all registered prompt versions."""
    return list(PROMPT_VERSIONS.keys())