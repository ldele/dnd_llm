import pytest
from engine.state import init_state
from engine.actions import player_defend, player_flee  # ← add this
import engine.actions as actions
import engine.combat as combat


def test_player_attack_reduces_enemy_hp():
    state = init_state()
    initial_hp = state.enemies[0].hp
    results = combat.player_attack(state)
    assert state.enemies[0].hp == initial_hp - results[0].damage


def test_miss_deals_no_damage():
    state = init_state()
    initial_hp = state.enemies[0].hp
    combat.roll_d20 = lambda: 1
    results = combat.player_attack(state)  # call via module, not imported function
    assert results[0].damage == 0
    assert state.enemies[0].hp == initial_hp


def test_victory_status_on_kill():
    state = init_state()
    state.enemies[0].hp = 1
    combat.roll_d20 = lambda: 20
    combat.player_attack(state)
    assert state.status == "victory"


def test_action_logged():
    state = init_state()
    combat.player_attack(state)
    assert len(state.log) == 1
    assert state.log[0].actor == "player"


def test_defend_reduces_damage():
    state = init_state()
    actions.roll_d20 = lambda: 20  # ← patch actions, not combat
    _, enemy_logs = player_defend(state)
    assert enemy_logs[0].damage <= state.enemies[0].attack * 0.5 + 1


def test_defend_logs_two_entries():
    state = init_state()
    player_defend(state)
    assert len(state.log) == 2


def test_defend_defeat():
    state = init_state()
    state.player.hp = 1
    actions.roll_d20 = lambda: 20
    player_defend(state)
    assert state.status == "defeat"


def test_flee_success():
    state = init_state()
    actions.roll_d20 = lambda: 20  # ← patch actions
    flee_log = player_flee(state)
    assert flee_log.action == "flee_success"
    assert state.status == "fled"


def test_flee_fail_enemy_attacks():
    state = init_state()
    actions.roll_d20 = lambda: 1
    player_flee(state)
    assert state.log[0].action == "flee_fail"
    assert len(state.log) == 2