"""
dnd_llm · engine/actions.py
============================
Non-combat action resolvers.

Design rule: all outcomes are deterministic.
The LLM narrates results — it never decides them.

Actions
-------
- defend : reduce incoming damage this turn by half
- flee   : attempt to escape (d20 vs threshold)
"""

from engine.state import GameState, ActionLog
from engine.combat import roll_d20, enemy_attack, living_enemies

FLEE_THRESHOLD = 10
DEFEND_REDUCTION = 0.5


def player_defend(state: GameState) -> tuple[ActionLog, list[ActionLog]]:
    """
    Player defends — all living enemies attack at half damage.
    Returns (defend_log, list of enemy logs).
    """
    defend_log = ActionLog(
        turn=state.turn,
        actor="player",
        roll=0,
        damage=0,
        action="defend",
    )
    state.log.append(defend_log)

    enemy_logs = []
    for enemy in living_enemies(state):
        roll = roll_d20()
        raw_damage = enemy.attack if roll >= 10 else 0
        reduced = int(raw_damage * DEFEND_REDUCTION)
        state.player.hp -= reduced

        log = ActionLog(
            turn=state.turn,
            actor=enemy.name,
            roll=roll,
            damage=reduced,
            action="attack",
        )
        state.log.append(log)
        enemy_logs.append(log)

        if state.player.hp <= 0:
            state.status = "defeat"
            break

    return defend_log, enemy_logs


def player_flee(state: GameState) -> ActionLog:
    """
    Player attempts to flee.
    Success: status = 'fled'.
    Failure: all enemies get a free attack.
    """
    roll = roll_d20()
    success = roll >= FLEE_THRESHOLD

    flee_log = ActionLog(
        turn=state.turn,
        actor="player",
        roll=roll,
        damage=0,
        action="flee_success" if success else "flee_fail",
    )
    state.log.append(flee_log)

    if success:
        state.status = "fled"
    else:
        enemy_attack(state)  # ← remove the extra loop, enemy_attack handles logging itself

    return flee_log