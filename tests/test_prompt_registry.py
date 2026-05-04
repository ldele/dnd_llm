from llm.prompt_registry import get_prompt, list_versions, ACTIVE_VERSION
from llm.prompts import build_system_prompt


def test_all_versions_registered():
    versions = list_versions()
    assert "v1.0" in versions
    assert "v1.1" in versions


def test_get_prompt_returns_valid_entry():
    entry = get_prompt("v1.0")
    assert "system" in entry
    assert "notes" in entry
    assert "version" in entry


def test_get_prompt_raises_on_unknown():
    import pytest
    with pytest.raises(ValueError):
        get_prompt("v99.0")


def test_active_version_is_registered():
    assert ACTIVE_VERSION in list_versions()


def test_v10_builds_without_voice():
    system = build_system_prompt(enemy_type="goblin", version="v1.0")
    assert "goblin" not in system  # v1.0 has no voice injection
    assert "dungeon master" in system.lower()


def test_v11_injects_voice():
    system = build_system_prompt(enemy_type="goblin", version="v1.1")
    assert "chaotic" in system.lower()  # goblin voice style