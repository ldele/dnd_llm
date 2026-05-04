#! C:\Users\LDELEZ\Documents\GitHub\dnd_llm\engine\combat.py python3
import random
from .state import GameState, ActionLog


def roll_d20() -> int:
    return random.randint(1, 20)


def living_enemies(state: GameState) -> list[Fighter]:
    return [e for e in state.enemies if e.hp > 0]


def player_attack(state: GameState) -> list[ActionLog]:
    """
    Player attacks ALL living enemies once.
    Returns a list of ActionLog — one per enemy hit.
    """
    results = []
    for enemy in living_enemies(state):
        roll = roll_d20()
        damage = state.player.attack if roll >= 10 else 0
        enemy.hp -= damage

        result = ActionLog(
            turn=state.turn,
            actor="player",
            roll=roll,
            damage=damage,
            action="attack",
        )
        state.log.append(result)
        results.append(result)

    if all(e.hp <= 0 for e in state.enemies):
        state.status = "victory"

    return results


def enemy_attack(state: GameState) -> list[ActionLog]:
    """
    Each living enemy attacks the player.
    Returns a list of ActionLog — one per enemy.
    """
    results = []
    for enemy in living_enemies(state):
        roll = roll_d20()
        damage = enemy.attack if roll >= 10 else 0
        state.player.hp -= damage

        result = ActionLog(
            turn=state.turn,
            actor=enemy.name,
            roll=roll,
            damage=damage,
            action="attack",
        )
        state.log.append(result)
        results.append(result)

        if state.player.hp <= 0:
            state.status = "defeat"
            break

    return results