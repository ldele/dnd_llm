#! C:\Users\LDELEZ\Documents\GitHub\dnd_llm\tests\test_combat.py python3
import pytest
from engine.state import init_state
from engine.combat import player_attack, enemy_attack


def test_player_attack_reduces_enemy_hp():
    state = init_state()
    initial_hp = state.enemy.hp
    result = player_attack(state)
    assert state.enemy.hp == initial_hp - result.damage


def test_miss_deals_no_damage():
    state = init_state()
    initial_hp = state.enemy.hp
    # Force a miss by monkeypatching
    import engine.combat as combat
    combat.roll_d20 = lambda: 1
    result = player_attack(state)
    assert result.damage == 0
    assert state.enemy.hp == initial_hp


def test_victory_status_on_kill():
    state = init_state()
    state.enemy.hp = 1
    import engine.combat as combat
    combat.roll_d20 = lambda: 20
    player_attack(state)
    assert state.status == "victory"


def test_defeat_status_on_death():
    state = init_state()
    state.player.hp = 1
    import engine.combat as combat
    combat.roll_d20 = lambda: 20
    enemy_attack(state)
    assert state.status == "defeat"


def test_action_logged():
    state = init_state()
    player_attack(state)
    assert len(state.log) == 1
    assert state.log[0].actor == "player"