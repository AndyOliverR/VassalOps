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

## Quick start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com/) installed locally
- Windows (primary target)

```bash
pip install -r requirements.txt
```

### Run

```bash
git clone https://github.com/AndyOliverR/VassalOps.git
cd VassalOps
python app.py
```

Or use `launch_engine.bat` / `launch_vassalops.bat`. The engine launcher starts the local UI only; it does **not** open an HTTP dashboard or the WebSocket broker on the LAN.

### Optional broker

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
