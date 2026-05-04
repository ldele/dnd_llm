import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from engine.state import init_state, DebugEntry, Fighter, NarrationEval
from engine.combat import player_attack, enemy_attack
from llm.narrator import narrate
from llm.memory import get_memory_block
from llm.prompts import build_user_prompt, serialize_state, build_context_usage


# ---------------------------------------------------------------------------
# Scenarios (enemy to fight)
# ---------------------------------------------------------------------------

SCENARIOS = {
    "Goblin Ambush": {
        "enemy": Fighter(name="Goblin", hp=10, max_hp=10, attack=3, enemy_type="goblin")
    },
    "Orc Warlord": {
        "enemy": Fighter(name="Orc Warlord", hp=20, max_hp=20, attack=6, enemy_type="orc_warrior")
    },
    "Skeleton Guard": {
        "enemy": Fighter(name="Skeleton", hp=8, max_hp=8, attack=4, enemy_type="skeleton")
    },
    "Ancient Dragon": {
        "enemy": Fighter(name="Ancient Dragon", hp=40, max_hp=40, attack=10, enemy_type="dragon")
    },
}


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
# Scenario selector (only shown before game starts)
# ---------------------------------------------------------------------------

if not st.session_state.log and state.turn == 1:
    scenario_name = st.selectbox("Choose your enemy", list(SCENARIOS.keys()))
    selected = SCENARIOS[scenario_name]
    st.session_state.game.enemy = selected["enemy"]

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
                narration_result, raw, eval_result, context_usage = narrate(state, result, memory_block)
                st.session_state.log.append(narration_result)
                st.session_state.narration_log.append(narration_result.narration)
                st.session_state.debug_log.append(DebugEntry(
                    turn=state.turn,
                    actor="player",
                    prompt=prompt,
                    raw_llm_output=raw,
                    parsed=narration_result,
                    state_snapshot=serialize_state(state),
                    eval_result=eval_result,
                    context_usage=context_usage,
                ))

                # Enemy turn (if still alive)
                if state.status == "ongoing":
                    result = enemy_attack(state)
                    prompt = build_user_prompt(state, result, memory_block)
                    narration_result, raw, eval_result, context_usage = narrate(state, result, memory_block)
                    st.session_state.log.append(narration_result)
                    st.session_state.narration_log.append(narration_result.narration)
                    st.session_state.debug_log.append(DebugEntry(
                        turn=state.turn,
                        actor=state.enemy.name,
                        prompt=prompt,
                        raw_llm_output=raw,
                        parsed=narration_result,
                        state_snapshot=serialize_state(state),
                        eval_result=eval_result,
                        context_usage=context_usage,
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
# Eval summary bar (always visible after first turn)
# ---------------------------------------------------------------------------

if st.session_state.debug_log:
    total = len(st.session_state.debug_log)
    passed = sum(1 for e in st.session_state.debug_log if e.eval_result.passed)
    pass_rate = passed / total

    st.markdown("### 📊 Eval Summary")
    col_e1, col_e2, col_e3 = st.columns(3)
    col_e1.metric("Turns evaluated", total)
    col_e2.metric("Passed", passed)
    col_e3.metric("Pass rate", f"{pass_rate:.0%}")


# ---------------------------------------------------------------------------
# Debug panel
# ---------------------------------------------------------------------------


with st.expander("🔍 Debug Panel", expanded=False):
    if not st.session_state.debug_log:
        st.caption("No turns yet. Attack to generate debug data.")
    else:
        for entry in reversed(st.session_state.debug_log):
            # Header with pass/fail badge
            status = "✅ PASS" if entry.eval_result.passed else "❌ FAIL"
            st.markdown(f"**Turn {entry.turn} — {entry.actor}** {status}")

            # Token usage
            cu = entry.context_usage
            st.markdown(
                f"`system`: {cu['system_tokens']} tokens  "
                f"`prompt`: {cu['prompt_tokens']} tokens  "
                f"`total`: {cu['total_tokens']} / {cu['context_limit']}  "
                f"`budget used`: {cu['budget_used_pct']}%"
            )

            # Eval details
            ev = entry.eval_result
            st.markdown(
                f"`hp_mentioned`: {'❌' if ev.hp_mentioned else '✅'}  "
                f"`sentences`: {ev.sentence_count}  "
                f"`format_valid`: {'✅' if ev.format_valid else '❌'}  "
                f"`fallback_used`: {'❌' if ev.fallback_used else '✅'}"
            )

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

# ---------------------------------------------------------------------------
# Session export
# ---------------------------------------------------------------------------

if st.session_state.debug_log:
    import json

    session_data = {
        "scenario": state.enemy.name,
        "turns": state.turn,
        "status": state.status,
        "eval_summary": {
            "total": len(st.session_state.debug_log),
            "passed": sum(1 for e in st.session_state.debug_log if e.eval_result.passed),
        },
        "entries": [e.model_dump() for e in st.session_state.debug_log],
    }

    st.download_button(
        label="📥 Export session as JSON",
        data=json.dumps(session_data, indent=2),
        file_name=f"session_turn{state.turn}_{state.enemy.name.lower().replace(' ', '_')}.json",
        mime="application/json",
    )

