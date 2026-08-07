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

**Tagline:** *Your PC’s workday — taught by you, approved by you, run locally.*

### One-time prerequisites
1. Install [Python 3.11+](https://www.python.org/downloads/) (check **Add python.exe to PATH**).
2. Install [Ollama](https://ollama.com/).

### Install & run
1. Clone or unzip VassalOps onto the PC (example: `C:\VassalOps`).
2. **Right-click `install_vassalops.ps1` → Run with PowerShell** (once). It installs Python packages, checks Ollama, pulls a usable model if needed, and creates a Desktop shortcut.
3. Or double-click **`bootstrap_and_run.bat`** / **`VassalOps.exe`** (build with `packaging\build_launcher.ps1`).
4. Type an instruction → review the **plain-English** plan → **Approve** or **Reject**. Watch the progress panel; use **Stop** or **Continue** if it pauses (MFA / missing window).

If something fails, read `storage\launch.log`. Prefer `VassalOps.exe` from `packaging\build_launcher.ps1` over the old stub `VassalOpsLaunch.exe`.

### What you can ask
- Simple facts: “what’s the date?”
- Desktop help via the local model (clicks/typing only after Approve)
- **60-second demo:** `import demo pack` → `run duty demo notepad hello` → Approve
- **Learn a one-off macro:** `learn my_login` → Approve → perform the task → press Escape
- **Replay macro:** `fetch my_login` → Approve

### Train your workday (Daily Duties)
Goal: show VassalOps what you do once, then run those duties each morning with one Approve.

1. `teach morning email` → **Approve** → do the email check yourself → press **Escape** to stop recording.  
   (Keystrokes are recorded — avoid typing passwords when possible.)
2. Repeat for other duties (`teach sap check`, etc.).
3. `build my workday` — schedules all taught duties into today’s playlist.
4. Open **Daily Duties** in the UI (or say `my workday`) → check items → **Approve today's run**.
5. Or chat: `run my workday` → Approve (stops on first failure; pauses if a window/landmark is missing).

Replay prefers **window-title focus** (and optional OCR landmarks) before raw coordinates. If MFA/CAPTCHA blocks a step, VassalOps **pauses** and asks you to Continue.

Optional weekday auto-open (briefing only, never silent autopilot):

```bat
register_morning_briefing.bat
```

Duties live in `storage/duties/`. Sample packs: `storage/duties/packs/`. This is **not** full unsupervised “become me” — UI drift, MFA, and CAPTCHAs still need you.

### Build the desktop launcher EXE
```bat
powershell -ExecutionPolicy Bypass -File packaging\build_launcher.ps1
```
Produces `VassalOps.exe` next to the repo (thin launcher that starts bootstrap).

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
