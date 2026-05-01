#! C:\Users\LDELEZ\Documents\GitHub\dnd_llm\engine\combat.py python3
import random
from .state import GameState, ActionLog


def roll_d20() -> int:
    return random.randint(1, 20)


def player_attack(state: GameState) -> ActionLog:
    roll = roll_d20()
    damage = state.player.attack if roll >= 10 else 0
    state.enemy.hp -= damage

    result = ActionLog(turn=state.turn, actor="player", roll=roll, damage=damage)
    state.log.append(result)

    if state.enemy.hp <= 0:
        state.status = "victory"

    return result


def enemy_attack(state: GameState) -> ActionLog:
    roll = roll_d20()
    damage = state.enemy.attack if roll >= 10 else 0
    state.player.hp -= damage

    result = ActionLog(turn=state.turn, actor="enemy", roll=roll, damage=damage)
    state.log.append(result)

    if state.player.hp <= 0:
        state.status = "defeat"

    return result