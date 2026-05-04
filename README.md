# ⚔ LLM Dungeon & Dragon

A dungeon crawler where game logic is fully deterministic and an LLM acts purely as a narrator.

> **Core idea: the engine decides truth. The LLM explains it.**

---

## What this project demonstrates

- Clean separation between deterministic game logic and AI narration
- Controlled, constrained use of LLMs — the model never touches game state
- Structured JSON output with Pydantic validation and graceful fallback
- Per-character voice profiles — prompt engineering for stylistically distinct narration
- Automatic evaluation layer — every narration is checked against its own constraints
- Bounded context management via rolling memory summarization
- Token budget tracking — context usage estimated and logged per call
- Production-grade reliability — exponential backoff retry on API failure
- Full observability — every prompt, raw response, eval result, and token count is traceable
- Session export — full debug data downloadable as JSON for offline analysis

---

## Architecture

```
Button click → engine step → LLM narration (retry + memory + voice) → eval → UI refresh
```

| Layer | Role | Tech |
|---|---|---|
| `engine/` | Dice rolls, combat, state | Pure Python + Pydantic |
| `llm/` | Narration, prompts, memory, eval | Anthropic API |
| `ui/` | Interactive interface | Streamlit |
| `tests/` | Engine + evaluator unit tests | pytest |

**The LLM never modifies state. State is the single source of truth.**

---

## Project Structure

```
dnd_llm/
│
├── engine/
│   ├── state.py        # GameState, Fighter, NarrationResult, DebugEntry, NarrationEval
│   ├── combat.py       # Dice rolls, attack logic
│   └── actions.py
│
├── llm/
│   ├── narrator.py     # narrate() — retry logic, returns (result, raw, eval, context)
│   ├── prompts.py      # Templates, serializer, voice profiles, token budget
│   ├── evaluator.py    # Automatic constraint checking on every narration
│   └── memory.py       # Rolling summarization, context management
│
├── ui/
│   └── app.py          # Streamlit UI — scenario selector, eval bar, debug panel, export
│
├── game/
│   └── loop.py         # CLI fallback for engine debugging
│
├── tests/
│   ├── test_combat.py
│   ├── test_prompts.py
│   └── test_evaluator.py
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

18 tests covering the deterministic engine, prompt parsing, and the evaluation layer. LLM calls are not unit tested — they are validated via the CLI smoke test, the in-app eval summary, and the session export.

---

## Features

### Scenario selector
Choose your enemy before the fight begins. Each enemy has distinct stats and a unique narration voice:

| Scenario | Enemy | HP | Attack | Voice |
|---|---|---|---|---|
| Goblin Ambush | Goblin | 10 | 3 | Chaotic, crude, desperate |
| Orc Warlord | Orc Warlord | 20 | 6 | Brutal, proud, honour-focused |
| Skeleton Guard | Skeleton | 8 | 4 | Cold, mechanical, ancient |
| Ancient Dragon | Ancient Dragon | 40 | 10 | Contemptuous, grand, slow |

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

### Observability debug panel
Expand the debug panel at any point to inspect every turn:

- Pass/fail status with per-check breakdown
- Token usage vs context budget
- Exact state snapshot sent (semantic labels, not raw numbers)
- Full prompt sent to the LLM
- Raw JSON string the model returned
- Parsed and validated `NarrationResult`

### Session export
Download the complete session as a structured JSON file — including all prompts, raw responses, eval results, and token counts. Useful for offline analysis and sharing demos.

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

The system prompt is generated dynamically per enemy type, injecting a voice profile and a few-shot example:

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

## CV Positioning

This project demonstrates:

- **System design** — deterministic core with a controlled AI presentation layer
- **LLM engineering** — structured output, constraint enforcement, fallback handling
- **Prompt engineering** — dynamic voice profiles, few-shot examples, semantic serialization
- **Observability** — full traceability of every LLM interaction
- **Evaluation** — automated constraint checking without human review
- **Production awareness** — retry logic, token budgeting, graceful degradation

---

## Roadmap

- [ ] Multiple simultaneous enemies
- [ ] Inventory and item system
- [ ] Spells and abilities
- [ ] Defend and flee actions
- [ ] Prompt versioning and A/B comparison
- [ ] LLM-as-judge hallucination detection
- [ ] Procedural dungeon rooms
- [ ] Save / load game state

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