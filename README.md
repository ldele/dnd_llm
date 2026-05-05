# ⚔ LLM Dungeon & Dragon

A dungeon crawler where game logic is fully deterministic and an LLM acts purely as a narrator.

> **Core idea: the engine decides truth. The LLM explains it.**

---

## What this project demonstrates

- Clean separation between deterministic game logic and AI narration
- Controlled, constrained use of LLMs — the model never touches game state
- Structured JSON output with Pydantic validation and graceful fallback
- Per-character voice profiles — prompt engineering for stylistically distinct narration
- Prompt versioning — prompts treated as versioned artifacts, not hardcoded strings
- Automatic evaluation layer — every narration checked against its own constraints
- Bounded context management via rolling memory summarization
- Token budget tracking — context usage estimated and logged per call
- Production-grade reliability — exponential backoff retry on API failure
- Full observability — every prompt, raw response, eval result, and token count is traceable
- Session export — full debug data downloadable as JSON for offline analysis
- Modular, extensible architecture — multiple enemies, defend, flee, all added without touching the LLM layer

---

## Architecture

```
Button click → engine step → LLM narration (retry + memory + voice) → eval → UI refresh
```

| Layer | Role | Tech |
|---|---|---|
| `engine/` | Dice rolls, combat, actions, state | Pure Python + Pydantic |
| `llm/` | Narration, prompts, memory, eval, registry | Anthropic API |
| `ui/` | Interactive interface | Streamlit |
| `tests/` | Engine + evaluator + prompt registry tests | pytest |

**The LLM never modifies state. State is the single source of truth.**

---

## Project Structure

```
dnd_llm/
│
├── engine/
│   ├── state.py        # GameState, Fighter, ActionLog, NarrationResult,
│   │                   # DebugEntry, NarrationEval
│   ├── combat.py       # Dice rolls, player/enemy attack (multi-enemy)
│   └── actions.py      # Defend and flee resolvers
│
├── llm/
│   ├── narrator.py     # narrate() — retry logic, returns (result, raw, eval, context, version)
│   ├── prompts.py      # Templates, state serializer, voice profiles, token budget
│   ├── prompt_registry.py  # Versioned prompt store (v1.0, v1.1)
│   ├── evaluator.py    # Automatic constraint checking on every narration
│   └── memory.py       # Rolling summarization, context management
│
├── ui/
│   └── app.py          # Streamlit UI — scenario selector, eval bar,
│                       # debug panel, streaming toggle, session export
│
├── game/
│   └── loop.py         # CLI fallback for engine debugging
│
├── tests/
│   ├── test_combat.py
│   ├── test_prompts.py
│   ├── test_evaluator.py
│   └── test_prompt_registry.py
│
├── main.py             # CLI entry point
├── .env                # API key (not committed)
└── README.md
```

---

## Quickstart

### 1. Clone and install

```bash
git clone https://github.com/yourname/dnd_llm.git
cd dnd_llm

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
```

### 2. Set your API key

Create a `.env` file at the project root:

```
ANTHROPIC_API_KEY=your_key_here
```

Get a key at [console.anthropic.com](https://console.anthropic.com/settings/keys).

### 3. Run the UI

```bash
streamlit run ui/app.py
```

### 4. Or run the CLI

```bash
python main.py
```

---

## Running Tests

```bash
pytest tests/ -v
```

28 tests covering the deterministic engine, prompt parsing, evaluation layer, and prompt registry. LLM calls are not unit tested — they are validated via the CLI smoke test, the in-app eval summary, and session export.

---

## Features

### Scenario selector
Choose your enemy before the fight begins. Each scenario has distinct stats, enemy count, and narration voice:

| Scenario | Enemies | Voice |
|---|---|---|
| Goblin Ambush | Goblin + Goblin Scout | Chaotic, crude, desperate |
| Orc Warlord | Orc Warlord | Brutal, proud, honour-focused |
| Skeleton Guard | Skeleton + Skeleton Archer | Cold, mechanical, ancient |
| Ancient Dragon | Ancient Dragon | Contemptuous, grand, slow |

### Multiple enemies
All living enemies attack each turn. Victory requires defeating every enemy. The engine loops over the enemy list — the LLM layer needed zero changes to support this.

### Combat actions

| Action | Effect |
|---|---|
| ⚔ Attack | Player attacks all living enemies. Each enemy counterattacks. |
| 🛡 Defend | Incoming damage halved this turn. All enemies still attack. |
| 🏃 Flee | Roll d20 ≥ 10 to escape. Failure = free enemy attack. |

### Prompt versioning
Prompts are versioned artifacts stored in `llm/prompt_registry.py`:

| Version | What changed |
|---|---|
| v1.0 | Basic constraints only — no voice injection |
| v1.1 | Per-character voice profile + few-shot example injected at runtime |

Select the active version from the UI before the fight. Each debug entry logs which version produced it.

### Tone-colored game log
Narration entries are colored by the LLM-returned tone field:

- 🟠 `tense` — the fight is balanced
- 🟢 `victorious` — a decisive blow
- 🔴 `grim` — taking heavy damage
- ⚫ `neutral` — a miss or uneventful turn

### Automatic evaluation layer
Every narration is checked against the constraints defined in the system prompt:

| Check | What it catches |
|---|---|
| `hp_mentioned` | LLM leaking raw HP numbers into prose |
| `sentence_count` | Output outside the 2-3 sentence constraint |
| `format_valid` | JSON response that couldn't be parsed |
| `fallback_used` | API failure or total parse failure |

A live eval summary bar shows total turns, passes, and pass rate across the session.

### Retry logic with exponential backoff
API calls retry up to 3 times (waits: 1s, 2s, 4s) before falling back to a deterministic narration. The game never crashes on a transient API error.

### Token budget tracking
Every narration call estimates token usage (system prompt + user prompt) and logs it against the context limit. Visible in the debug panel per turn.

### Streaming narration
Toggle streaming mode before the fight. Narration animates word by word instead of appearing all at once.

> Note: this uses client-side animation from a buffered response rather than true token streaming. True streaming with structured JSON output requires a custom text format — tracked in the roadmap.

### Observability debug panel
Expand the debug panel at any point to inspect every turn:

- Pass/fail status with per-check breakdown
- Prompt version used
- Token usage vs context budget
- Exact state snapshot sent (semantic labels, not raw numbers)
- Full prompt sent to the LLM
- Raw JSON string the model returned
- Parsed and validated `NarrationResult`

### Session export
Download the complete session as a structured JSON file — including all prompts, raw responses, eval results, and token counts.

---

## Design Rules

These are non-negotiable constraints that keep the architecture clean:

1. **LLM never modifies state** — narration is read-only
2. **Dice rolls are deterministic** — Python `random` only, never LLM
3. **State is the single source of truth** — Pydantic model, no duplication
4. **UI is stateless** — renders current state only, no logic
5. **Prompts describe outcomes** — the LLM is never asked to decide what happens
6. **State is serialized to semantic labels before reaching the LLM** — `hp=3` becomes `"bloodied"`, not a raw number

---

## LLM Prompt Strategy

The narrator receives a structured prompt built from three components:

- **Memory block** — a rolling summary of older turns + the last 3 turns verbatim
- **Game state** — semantic labels (e.g. `"critically wounded"`) not raw numbers
- **Action result** — what the engine computed (roll, damage, actor)

The system prompt is generated dynamically per enemy type and prompt version, injecting a voice profile and a few-shot example:

```
The enemy in this scene is an orc warlord.
Narrate their actions in a brutal and proud voice.
Vocabulary guidance: heavy, deliberate, honour-focused.
Example of correct tone: "The orc advances without flinching, each blow a statement of dominance."
```

Output is constrained to valid JSON:

```json
{
  "narration": "2-3 sentence description",
  "tone": "tense" | "victorious" | "grim" | "neutral",
  "hit": true | false
}
```

If the model returns invalid JSON after retries, a deterministic fallback fires — the game never crashes on a bad LLM response.

---

## Estimated API Cost

Using `claude-haiku-4-5-20251001` (~2 calls per turn):

| Session length | Estimated cost |
|---|---|
| 10 turns | < $0.01 |
| Full evening of testing | < $0.10 |

---

## Roadmap

- [ ] True streaming narration (custom text format, parse after stream closes)
- [ ] Prompt v1.2 — A/B comparison mode in UI
- [ ] Inventory and item system
- [ ] Spells and abilities
- [ ] Procedural dungeon rooms
- [ ] Save / load game state
- [ ] **Project 2** — agentic LLM system with tool-calling and RAG (separate repo)

---

## Requirements

```
anthropic
streamlit
pydantic
python-dotenv
pytest
```

Generate `requirements.txt`:

```bash
pip freeze > requirements.txt
```