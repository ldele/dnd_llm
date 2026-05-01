# ⚔ LLM Dungeon & Dragon

A dungeon crawler where game logic is fully deterministic and an LLM acts purely as a narrator.

> **Core idea: the engine decides truth. The LLM explains it.**

---

## What this project demonstrates

- Clean separation between deterministic game logic and AI narration
- Controlled, constrained use of LLMs — the model never touches game state
- Bounded context management via rolling memory summarization
- Modular architecture ready to extend (inventory, spells, multiple enemies)

---

## Architecture

```
Button click → engine step → LLM narration (with memory) → UI refresh
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
│   ├── state.py        # GameState Pydantic model
│   ├── combat.py       # Dice rolls, attack logic
│   └── actions.py
│
├── llm/
│   ├── narrator.py     # narrate() — single LLM call per action
│   ├── prompts.py      # Templates + state serializer
│   └── memory.py       # Rolling summarization, context management
│
├── ui/
│   └── app.py          # Streamlit interface
│
├── game/
│   └── loop.py         # CLI fallback for engine debugging
│
├── tests/
│   └── test_combat.py
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

Tests cover the deterministic engine only. LLM calls are not unit tested — they are validated manually via the CLI smoke test.

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

The system prompt constrains the model strictly:

```
- Use ONLY the facts given
- Do NOT mention HP numbers
- Do NOT invent enemies, items, or events
- Do NOT address the player
- Length: exactly 2-3 sentences
```

---

## Estimated API Cost

Using `claude-haiku-4-5-20251001` (~2 calls per turn):

| Session length | Estimated cost |
|---|---|
| 10 turns | < $0.01 |
| Full evening of testing | < $0.10 |

---

## Roadmap

- [ ] Multiple enemies
- [ ] Inventory system
- [ ] Spells and abilities
- [ ] Structured JSON output from narrator (drive UI effects from tone)
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
