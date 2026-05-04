from llm.evaluator import evaluate, _check_hp_mentioned, _count_sentences
from engine.state import NarrationResult


def _make_result(narration: str, tone="tense", hit=True) -> NarrationResult:
    return NarrationResult(narration=narration, tone=tone, hit=hit)


def test_hp_mentioned_catches_numeric():
    assert _check_hp_mentioned("You have 14 HP remaining.") is True
    assert _check_hp_mentioned("The goblin has 3/10 HP.") is True


def test_hp_mentioned_passes_clean_prose():
    assert _check_hp_mentioned("The hero staggers, badly wounded.") is False


def test_sentence_count_two():
    text = "The hero strikes true. The goblin staggers back."
    assert _count_sentences(text) == 2


def test_sentence_count_three():
    text = "The hero strikes. The goblin reels. Blood is drawn."
    assert _count_sentences(text) == 3


def test_eval_passes_clean_output():
    result = _make_result("The hero lands a solid blow. The goblin staggers, wounded.")
    raw = '{"narration": "...", "tone": "tense", "hit": true}'
    ev = evaluate(result, raw, fallback_used=False)
    assert ev.passed is True


def test_eval_fails_on_hp_leak():
    result = _make_result("The hero has 14 HP left and strikes hard.")
    raw = '{"narration": "...", "tone": "tense", "hit": true}'
    ev = evaluate(result, raw, fallback_used=False)
    assert ev.passed is False
    assert ev.hp_mentioned is True


def test_eval_fails_on_fallback():
    result = _make_result("The player strikes, dealing 5 damage.")
    ev = evaluate(result, "", fallback_used=True)
    assert ev.passed is False
    assert ev.fallback_used is True