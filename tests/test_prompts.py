from engine.state import NarrationResult
from llm.narrator import _parse
from engine.state import init_state
from engine.combat import player_attack
from llm.prompts import hp_label, serialize_state, serialize_result, build_user_prompt


def test_hp_label_boundaries():
    assert hp_label(0, 10) == "dead"
    assert hp_label(2, 10) == "critically wounded"
    assert hp_label(5, 10) == "bloodied"
    assert hp_label(8, 10) == "fresh"   # 8/10 = 0.80, correctly above 0.75
    assert hp_label(7, 10) == "injured" # 7/10 = 0.70, correctly below 0.75


def test_serialize_state_contains_labels():
    state = init_state()
    state.enemy.hp = 3  # bloodied
    output = serialize_state(state)
    assert "bloodied" in output
    assert "fresh" in output  # player is untouched


def test_build_user_prompt_no_raw_numbers_alone():
    state = init_state()
    import engine.combat as combat
    combat.roll_d20 = lambda: 20
    result = player_attack(state)
    prompt = build_user_prompt(state, result)
    # Semantic labels must be present
    assert "critical hit" in prompt
    assert "Game state" in prompt
    assert "Action result" in prompt

def test_parse_valid_json():
    state = init_state()
    result = player_attack(state)
    raw = '{"narration": "The hero strikes true.", "tone": "tense", "hit": true}'
    parsed = _parse(raw, result)
    assert isinstance(parsed, NarrationResult)
    assert parsed.hit is True
    assert parsed.tone == "tense"


def test_parse_invalid_json_returns_fallback():
    state = init_state()
    result = player_attack(state)
    parsed = _parse("This is not JSON at all.", result)
    assert isinstance(parsed, NarrationResult)  # fallback always returns valid object


def test_parse_strips_markdown_fences():
    state = init_state()
    result = player_attack(state)
    raw = '```json\n{"narration": "Strike!", "tone": "neutral", "hit": false}\n```'
    parsed = _parse(raw, result)
    assert parsed.narration == "Strike!"