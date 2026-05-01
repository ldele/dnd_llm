#! C:\Users\LDELEZ\Documents\GitHub\dnd_llm\engine\state.py python3
from pydantic import BaseModel, Field
from typing import List, Literal

class NarrationResult(BaseModel):
    narration: str
    tone: Literal["tense", "victorious", "grim", "neutral"]
    hit: bool

class Fighter(BaseModel):
    name: str
    hp: int
    max_hp: int
    attack: int


class ActionLog(BaseModel):
    turn: int
    actor: str
    roll: int
    damage: int
    narration: str = ""


class GameState(BaseModel):
    player: Fighter
    enemy: Fighter
    turn: int = 1
    log: List[ActionLog] = Field(default_factory=list)
    status: str = "ongoing"  # "ongoing" | "victory" | "defeat"


def init_state() -> GameState:
    return GameState(
        player=Fighter(name="Hero", hp=20, max_hp=20, attack=5),
        enemy=Fighter(name="Goblin", hp=10, max_hp=10, attack=3),
    )

class DebugEntry(BaseModel):
    turn: int
    actor: str
    prompt: str
    raw_llm_output: str
    parsed: NarrationResult
    state_snapshot: str  # serialized state at time of call