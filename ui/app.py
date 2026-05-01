import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from engine.state import init_state, DebugEntry
from engine.combat import player_attack, enemy_attack
from llm.narrator import narrate
from llm.memory import get_memory_block
from llm.prompts import build_user_prompt, serialize_state


# ---------------------------------------------------------------------------
# Session state bootstrap
# ---------------------------------------------------------------------------

if "game" not in st.session_state:
    st.session_state.game = init_state()

if "log" not in st.session_state:
    st.session_state.log = []           # list of NarrationResult objects

if "narration_log" not in st.session_state:
    st.session_state.narration_log = [] # flat list of narration strings for memory

if "summary" not in st.session_state:
    st.session_state.summary = ""

if "debug_log" not in st.session_state:
    st.session_state.debug_log = []  # list of DebugEntry objects


state = st.session_state.game


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

st.title("⚔ LLM Dungeon & Dragon")
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("🧙 Hero")
    st.progress(state.player.hp / state.player.max_hp)
    st.caption(f"{state.player.hp} / {state.player.max_hp} HP")

with col2:
    st.subheader(f"👹 {state.enemy.name}")
    st.progress(max(state.enemy.hp, 0) / state.enemy.max_hp)
    st.caption(f"{max(state.enemy.hp, 0)} / {state.enemy.max_hp} HP")

st.divider()

st.subheader(f"📜 Turn {state.turn}")

for entry in st.session_state.log:
    tone_icon = {
        "victorious": "⚡",
        "grim": "💀",
        "tense": "⚔",
        "neutral": "·",
    }.get(entry.tone, "·")

    color = {
        "victorious": "#4CAF50",
        "grim": "#f44336",
        "tense": "#FF9800",
        "neutral": "#aaaaaa",
    }.get(entry.tone, "#aaaaaa")

    st.markdown(
        f"<span style='color:{color}'>{tone_icon} *{entry.narration}*</span>",
        unsafe_allow_html=True,
    )

st.divider()


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

if state.status == "ongoing":
    col_a, col_b = st.columns([1, 1])

    with col_a:
        if st.button("⚔ Attack", use_container_width=True):
            with st.spinner("The Dungeon Master narrates..."):

                memory_block, st.session_state.summary = get_memory_block(
                    st.session_state.narration_log,
                    st.session_state.summary,
                    state.turn,
                )

                # Player turn
                result = player_attack(state)
                prompt = build_user_prompt(state, result, memory_block)
                narration_result, raw = narrate(state, result, memory_block)
                st.session_state.log.append(narration_result)
                st.session_state.narration_log.append(narration_result.narration)
                st.session_state.debug_log.append(DebugEntry(
                    turn=state.turn,
                    actor="player",
                    prompt=prompt,
                    raw_llm_output=raw,
                    parsed=narration_result,
                    state_snapshot=serialize_state(state),
                ))

                # Enemy turn (if still alive)
                if state.status == "ongoing":
                    result = enemy_attack(state)
                    prompt = build_user_prompt(state, result, memory_block)
                    narration_result, raw = narrate(state, result, memory_block)
                    st.session_state.log.append(narration_result)
                    st.session_state.narration_log.append(narration_result.narration)
                    st.session_state.debug_log.append(DebugEntry(
                        turn=state.turn,
                        actor=state.enemy.name,
                        prompt=prompt,
                        raw_llm_output=raw,
                        parsed=narration_result,
                        state_snapshot=serialize_state(state),
                    ))

                state.turn += 1
            st.rerun()

    with col_b:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.game = init_state()
            st.session_state.log = []
            st.session_state.narration_log = []
            st.session_state.summary = ""
            st.session_state.debug_log = []
            st.rerun()

elif state.status == "victory":
    st.success("⚔ The enemy falls. Victory!")
    if st.button("🔄 Play again"):
        st.session_state.game = init_state()
        st.session_state.log = []
        st.session_state.narration_log = []
        st.session_state.summary = ""
        st.session_state.debug_log = []
        st.rerun()

elif state.status == "defeat":
    st.error("💀 You have been slain.")
    if st.button("🔄 Play again"):
        st.session_state.game = init_state()
        st.session_state.log = []
        st.session_state.narration_log = []
        st.session_state.summary = ""
        st.session_state.debug_log = []
        st.rerun()

# ---------------------------------------------------------------------------
# Debug panel
# ---------------------------------------------------------------------------

with st.expander("🔍 Debug Panel", expanded=False):
    if not st.session_state.debug_log:
        st.caption("No turns yet. Attack to generate debug data.")
    else:
        for entry in reversed(st.session_state.debug_log):
            st.markdown(f"**Turn {entry.turn} — {entry.actor}**")

            col_left, col_right = st.columns(2)

            with col_left:
                st.markdown("**State snapshot**")
                st.code(entry.state_snapshot, language="text")

                st.markdown("**Parsed output**")
                st.json(entry.parsed.model_dump())

            with col_right:
                st.markdown("**Prompt sent**")
                st.code(entry.prompt, language="text")

                st.markdown("**Raw LLM response**")
                st.code(entry.raw_llm_output, language="json")

            st.divider()