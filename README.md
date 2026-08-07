# <img src="storage/dashboard/vassal_icon.png" alt="" width="48" height="48" align="left" /> VassalOps

<br clear="all" />

**Your PC’s workday — taught by you, approved by you, run locally.**

[![CI](https://github.com/AndyOliverR/VassalOps/actions/workflows/ci.yml/badge.svg)](https://github.com/AndyOliverR/VassalOps/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Issues](https://img.shields.io/github/issues/AndyOliverR/VassalOps)](https://github.com/AndyOliverR/VassalOps/issues)

Local-first **Windows** desktop agent: a pywebview control panel, LangGraph planning, local Ollama, and pyautogui automation — with a human **bot-sitter Approve gate** before mouse/keyboard actions run.

Data stays on your machine by default. Optional network features bind to **localhost** and require a shared token.

---

## What it is / is not

| It is | It is not |
|-------|-----------|
| A teachable **workday** runner for your Windows PC | A cloud chatbot that holds your company data |
| **Approve → run** desktop automation you can watch and Stop | Silent unsupervised “become me” autopilot |
| Complementary to chat/gateway agents (e.g. multi-channel assistants) | A clone of multi-OS messaging gateways |

---

## Install

**Prerequisites:** [Python 3.11+](https://www.python.org/downloads/) (Add to PATH) and [Ollama](https://ollama.com/).

**Windows (recommended one-shot):**

```powershell
# From the VassalOps folder after clone/unzip
powershell -ExecutionPolicy Bypass -File .\install_vassalops.ps1
```

That installs packages, checks Ollama, and creates a Desktop shortcut to `bootstrap_and_run.bat`.

**Or launch directly:**

```bat
bootstrap_and_run.bat
```

Prefer the `.bat` path. Unsigned `VassalOps.exe` builds often trigger antivirus false positives — see [Antivirus false positives](#antivirus-false-positives-k7-windows-defender-etc). Do not use the old stub `VassalOpsLaunch.exe`.

---

## Quick start

1. Open VassalOps (Desktop shortcut or `bootstrap_and_run.bat`).
2. In chat, type: `import demo pack`
3. Type: `run duty demo notepad hello`
4. Review the **plain-English** plan → **Approve**
5. Watch the progress panel (use **Stop** or **Continue** if it pauses)

You should see Notepad open and type a short greeting. That is the 60-second demo.

**Train your real workday**

1. `teach morning email` → Approve → do the task yourself → press **Escape**
2. Repeat for other duties → `build my workday`
3. Next morning: **Daily Duties** → **Approve today's run** (or `run my workday`)

Optional weekday briefing only (never silent run): `register_morning_briefing.bat`

---

## How it fits together

```text
capture_context -> parse_intent -> [human Approve] -> execute -> audit ledger
```

- **Control UI** — pywebview loads `storage/dashboard/`; chat + Daily Duties + live progress / Stop / stuck Continue
- **Planner** — LangGraph in `app.py` + local Ollama JSON steps (plain-English checklist in the Approve UI)
- **Bot-sitter** — nothing desktop-destructive runs until you Approve (or Approve today's playlist)
- **Duties** — teach/replay under `storage/duties/`; morning playlist in `playlist.json`
- **Landmarks** — replay prefers window-title focus (and optional OCR text) before raw coordinates; pauses if missing
- **ToolRouter** — in-process backup/sort dispatcher — **not** MCP process isolation
- **Broker** — optional WebSocket on `127.0.0.1` with token — **off by default**
- **Ledger / sleep-time** — audit rows can feed preferences in `storage/agent.md`

---

## Security

Treat every proposed plan as untrusted until you read it. Desktop automation runs **as your Windows user**.

- **Approve required** before teach, fetch, duty run, or playlist run
- **Stuck / MFA pause** — missing window or landmark freezes automation and asks you to Continue (no silent smash-through)
- **Broker** stays on localhost + shared token when enabled
- **Teach mode** can record keystrokes (including passwords) — prefer click-only for logins; we warn in UI
- **No silent autopilot by default** — morning Task Scheduler only opens the briefing UI

Full policy and reporting: **[SECURITY.md](SECURITY.md)**

Security practices for local agents are inspired by community guidance (including projects like [OpenClaw](https://github.com/openclaw/openclaw)’s emphasis on untrusted input and host-tool risk)—adapted here for **Windows desktop Approve/duty** workflows.

---

## Documentation

| Goal | Start here |
|------|------------|
| Install & run on Windows | [Install](#install), `install_vassalops.ps1` |
| 60-second demo | [Quick start](#quick-start), `storage/duties/packs/` |
| Train Daily Duties | [Quick start](#quick-start) → train section |
| Antivirus false positives | [below](#antivirus-false-positives-k7-windows-defender-etc) |
| Threat model & vulnerability reports | [SECURITY.md](SECURITY.md) |
| Contribute / good first issues | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Architecture honesty | [How it fits together](#how-it-fits-together) |

### Antivirus false positives (K7, Windows Defender, etc.)

Teach/replay uses keyboard/mouse hooks and desktop control; unsigned PyInstaller EXEs look like packed malware to many AVs. That is usually a **heuristic false positive**, not proof of a spyware payload in this repo.

1. Check **Reports** for the exact path.
2. If it is under your VassalOps folder → restore + **folder exclusion** for that root.
3. Keep launching with `bootstrap_and_run.bat`.
4. Do not disable antivirus globally.

---

## Development

```bash
git clone https://github.com/AndyOliverR/VassalOps.git
cd VassalOps
pip install -r requirements.txt
set PYTHONPATH=%CD%
python -m unittest discover -s tests -p "test_*.py"
python app.py
```

Optional broker (token from `config.json`):

```bash
python src/communication/socket_broker.py
```

Optional EXE packaging (dev only; exclude folder in AV first): `packaging\build_launcher.ps1`

See [CONTRIBUTING.md](CONTRIBUTING.md). AI-assisted PRs are welcome when tests pass and README/security claims stay honest.

---

## Community and funding

- **Bugs & ideas:** [GitHub Issues](https://github.com/AndyOliverR/VassalOps/issues) (look for `good first issue`)
- **Pull requests:** [CONTRIBUTING.md](CONTRIBUTING.md)
- **Sponsor:** GitHub Sponsors via [FUNDING.yml](.github/FUNDING.yml) (`AndyOliverR`) when enabled on the account

Pitch for operators and funders: a **work-PC-safe** local agent with human Approve and teachable duties — compliance-friendlier than chat agents that run host tools unchecked.

---

## License

MIT — see [LICENSE](LICENSE).
