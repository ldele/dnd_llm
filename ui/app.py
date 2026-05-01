import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from engine.state import init_state
from engine.combat import player_attack, enemy_attack
from llm.narrator import narrate
from llm.memory import get_memory_block


# ---------------------------------------------------------------------------
# Session state bootstrap
# ---------------------------------------------------------------------------

if "game" not in st.session_state:
    st.session_state.game = init_state()

if "log" not in st.session_state:
    st.session_state.log = []          # list of (actor, narration) tuples

if "narration_log" not in st.session_state:
    st.session_state.narration_log = [] # flat list of narration strings for memory

if "summary" not in st.session_state:
    st.session_state.summary = ""


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

for actor, text in st.session_state.log:
    if actor == "player":
        st.markdown(f"🗡 *{text}*")
    else:
        st.markdown(f"💢 *{text}*")

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
                narration = narrate(state, result, memory_block)
                st.session_state.log.append(("player", narration))
                st.session_state.narration_log.append(narration)

                # Enemy turn (if still alive)
                if state.status == "ongoing":
                    result = enemy_attack(state)
                    narration = narrate(state, result, memory_block)
                    st.session_state.log.append(("enemy", narration))
                    st.session_state.narration_log.append(narration)

                state.turn += 1
            st.rerun()

    with col_b:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.game = init_state()
            st.session_state.log = []
            st.session_state.narration_log = []
            st.session_state.summary = ""
            st.rerun()

elif state.status == "victory":
    st.success("⚔ The enemy falls. Victory!")
    if st.button("🔄 Play again"):
        st.session_state.game = init_state()
        st.session_state.log = []
        st.session_state.narration_log = []
        st.session_state.summary = ""
        st.rerun()

elif state.status == "defeat":
    st.error("💀 You have been slain.")
    if st.button("🔄 Play again"):
        st.session_state.game = init_state()
        st.session_state.log = []
        st.session_state.narration_log = []
        st.session_state.summary = ""
        st.rerun()