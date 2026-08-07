# VassalOps

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

Local-first desktop agent for Windows: a **pywebview** control panel, **LangGraph** planning, local **Ollama** inference, and **pyautogui** automation — with a human bot-sitter approval gate before mouse/keyboard macros run.

Enterprise data stays on your machine by default. Optional network features bind to localhost and require a shared token.

---

## What it actually does

1. **Capture** — screen OCR / clipboard context for the planner.
2. **Parse** — local Ollama turns your instruction into structured action steps (JSON).
3. **Approve** — the dashboard shows proposed steps; you must **Approve** or **Reject** before execution.
4. **Execute** — approved steps run via pyautogui / macros / an in-process **ToolRouter** (backup, sort).

```text
capture_context -> parse_intent -> [human approve] -> execute_macros
```

---

## Architecture (honest)

| Piece | Reality |
|-------|---------|
| **UI** | pywebview loads `storage/dashboard/` and calls Python via `js_api` |
| **Planner** | Thin LangGraph graph in `app.py` with SQLite checkpointer (`gm_memory.db`, local) |
| **Model** | Ollama on `127.0.0.1:11434` (auto-started if missing from PATH) |
| **ToolRouter** | In-process dispatcher (`src/execution/tool_router.py`) — **not** Model Context Protocol process isolation |
| **Bot-sitter** | UI `confirm_plan` + optional broker console y/n |
| **Broker** | Optional WebSocket on `127.0.0.1:8765` with `broker_auth_token` from `config.json` — **not** started by default |
| **Sandbox runner** | Subprocess + timeout only — **not** an OS jail or container; scripts still run as your user |
| **Sleep-time / health** | Screener/Verifier read real rows from the audit ledger and may append preferences to `storage/agent.md` |

---

## Quick start (lay user)

### One-time prerequisites
1. Install [Python 3.11+](https://www.python.org/downloads/) (check **Add python.exe to PATH**).
2. Install [Ollama](https://ollama.com/) and ensure at least one model is available (this repo’s `config.json` defaults to `gpt-oss:120b-cloud` — change `model_configuration.active_model` to any model you have, e.g. `llama3`).

### Install & run
1. Clone or unzip VassalOps onto the PC (example: `C:\VassalOps`).
2. **Double-click `bootstrap_and_run.bat`** (or the Desktop **VassalOps** shortcut).
3. Wait while it quietly checks Python packages, starts Ollama if needed, verifies the model, then opens the chat window.
4. Type an instruction → review the proposed steps → **Approve** or **Reject**.

If something fails, read `storage\launch.log` (and any MessageBox). Do **not** use the old `VassalOpsLaunch.exe` stub — it is not a real installer.

### What you can ask
- Simple facts: “what’s the date?”
- Desktop help via the local model (clicks/typing only after Approve)
- **Learn a task:** `learn my_login` → Approve → perform the task → press Escape to stop recording
- **Replay:** `fetch my_login` → Approve

### Developer run
```bash
git clone https://github.com/AndyOliverR/VassalOps.git
cd VassalOps
pip install -r requirements.txt
python app.py
```

`launch_engine.bat` also goes through the same bootstrap path. Optional broker:

```bash
python src/communication/socket_broker.py
```

Clients must send JSON including `"token"` matching `runtime_boundaries.broker_auth_token` in `config.json`.

---

## Safety notes

- Desktop automation can click and type as you. Never approve a plan you have not read.
- OCR/clipboard text is redacted before model prompts where possible; treat screen content as sensitive.
- Do not commit local `*.db` files, binaries, or `build/` / `dist/` artifacts.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT — see [LICENSE](LICENSE).
