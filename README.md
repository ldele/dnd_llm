# ⚔ LLM Dungeon & Dragon

A dungeon crawler where game logic is fully deterministic and an LLM acts purely as a narrator.

> **Core idea: the engine decides truth. The LLM explains it.**

---

## What this project demonstrates

- Clean separation between deterministic game logic and AI narration
- Controlled, constrained use of LLMs — the model never touches game state
- Structured JSON output with Pydantic validation and graceful fallback
- Per-character voice profiles — prompt engineering for stylistically distinct narration
- Bounded context management via rolling memory summarization
- Full observability — every prompt, raw LLM response, and parsed output is traceable
- Modular architecture ready to extend (inventory, spells, multiple enemies)

---

## Architecture

```
Button click → engine step → LLM narration (with memory + voice) → UI refresh
```

| Layer | Role | Tech |
|---|---|---|
| `engine/` | Dice rolls, combat, state | Pure Python + Pydantic |
| `llm/` | Narration, prompts, memory | Anthropic API |
| `ui/` | Interactive interface | Streamlit |
| `tests/` | Engine unit tests | pytest |

**The LLM never modifies state. State is the single source of truth.**

---

## Project Structure

```
dnd_llm/
│
├── engine/
│   ├── state.py        # GameState + Fighter + NarrationResult + DebugEntry models
│   ├── combat.py       # Dice rolls, attack logic
│   └── actions.py
│
├── llm/
│   ├── narrator.py     # narrate() — returns (NarrationResult, raw_output)
│   ├── prompts.py      # Templates, state serializer, character voice profiles
│   └── memory.py       # Rolling summarization, context management
│
├── ui/
│   └── app.py          # Streamlit interface with scenario selector + debug panel
│
├── game/
│   └── loop.py         # CLI fallback for engine debugging
│
├── tests/
│   ├── test_combat.py
│   └── test_prompts.py
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

11 tests covering the deterministic engine and prompt parsing logic. LLM calls are not unit tested — they are validated via the CLI smoke test and the in-app debug panel.

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

### Observability debug panel
Expand the debug panel at any point to inspect, for every turn:

- The exact state snapshot sent (semantic labels, not raw numbers)
- The full prompt sent to the LLM
- The raw JSON string the model returned
- The parsed and validated `NarrationResult`

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

The system prompt is generated dynamically per enemy type, injecting a voice profile and a few-shot example to enforce stylistic consistency:

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

If the model returns invalid JSON, a deterministic fallback fires — the game never crashes on a bad LLM response.

---

## Estimated API Cost

Using `claude-haiku-4-5-20251001` (~2 calls per turn):

| Session length | Estimated cost |
|---|---|
| 10 turns | < $0.01 |
| Full evening of testing | < $0.10 |

---

## Roadmap

- [ ] Multiple simultaneous enemies
- [ ] Inventory and item system
- [ ] Spells and abilities
- [ ] Defend and flee actions
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