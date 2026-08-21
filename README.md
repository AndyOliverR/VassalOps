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
| Complementary to chat/gateway agents and Buzz-class workspaces (team chat + coding agents) | A Slack/GitHub clone or multi-agent huddle product |

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

**Updates:** On launch, VassalOps checks [GitHub Releases](https://github.com/AndyOliverR/VassalOps/releases) and asks before applying. Duties, teach memory, and `config.json` are kept; dashboard + demo packs refresh. Set `VASSALOPS_SKIP_UPDATE=1` to disable. Maintainers: bump `VERSION`, commit, tag `vX.Y.Z` matching that file — CI publishes `VassalOps-X.Y.Z.zip`.

Prefer the `.bat` path. Unsigned `VassalOps.exe` builds often trigger antivirus false positives — see [Antivirus false positives](#antivirus-false-positives-k7-windows-defender-etc). Do not use the old stub `VassalOpsLaunch.exe`.

---

## Quick start

1. Open VassalOps (Desktop shortcut or `bootstrap_and_run.bat`).
2. In chat, type: `import demo pack`
3. Type: `run duty demo notepad hello`
4. Review the **plain-English** plan → **Approve**
5. Watch the progress panel (use **Stop** or **Continue** if it pauses)

You should see Notepad open and type a short greeting. That is the 60-second demo. Alternate: `run duty demo calculator one plus one`. Full script and GIF capture notes: [docs/DEMO.md](docs/DEMO.md). Chat `resume` later to continue the last saved goal (Approve still required for desktop tools).

**Train your real workday**

1. `teach morning email` → Approve → do the task yourself → press **Escape**
2. Repeat for other duties → `build my workday`
3. Next morning: **Daily Duties** → **Approve today's run** (or `run my workday`)

Optional weekday briefing only (never silent run): `register_morning_briefing.bat`

---

## How it fits together

An AI agent is an LLM that can use tools, running in a loop until the job is done. A chatbot only generates words. VassalOps is the latter plus **allowlisted desktop tools**, a **bounded think → tool → observe loop** (max 8 turns), and a human **Approve** gate.

```text
capture_context -> parse_intent -> [human Approve] -> agent loop (think/act/observe) -> audit ledger
```

- **Control UI** — pywebview loads `storage/dashboard/`; chat + Daily Duties + live progress / Stop / stuck Continue
- **Planner / loop** — LangGraph in `app.py` + local Ollama. Planner and agent-loop JSON is schema-validated locally (Instructor-style retry, not an Instructor cloud/SDK dependency). Free-form goals Approve once, then the harness runs tools and feeds results back into context
- **Loop engineering (safe subset)** — Inner loop = bounded `agent_loop` (max 8 turns) **after Approve**. Outer loop = Daily Duties / morning briefing, still **Approve before run**. Unsupervised Claude-style desktop loops (interval jobs that skip Approve) are out of scope.
- **Neuro-symbolic lite** — Pydantic schemas at the door, thin workday domain rules (Duty / Playlist / Window / Risk) after each tool, human Approve as the gate — **not** OWL/Neo4j
- **Autoresearch pattern (safe subset)** — Karpathy-style program / asset / score maps to human prefs + teach brief (`storage/agent.md`), duty JSON under `storage/duties/`, and locked scoring via `storage/runs/` evidence. Improve a duty only after Approve or re-teach — **not** unsupervised overnight desktop mutation (and not a vendored [autoresearch](https://github.com/karpathy/autoResearch) dependency)
- **Workflow redesign (safe subset)** — Productivity comes from redesigning the PC workday (teach duties, Approve, replay), not sprinkling an LLM on the old click-path. Steering context lives in `storage/agent.md` and duty JSON; the duty is the workday spec, checked via Approve and `storage/runs/` evidence. This is the same “redesign the workflow, don’t add a copilot” idea as [AWS/Kiro productivity talks](https://www.youtube.com/watch?v=zy4nmItGsxY) — **not** Amazon Q, Kiro, or unattended cloud agent fleets
- **Harness engineering (safe subset)** — VassalOps is the harness around local Ollama (allowlisted tools, `storage/agent.md` memory, bounded loops, firewall guardrails), but desktop actions still require **Approve**. Not unsupervised “run for months with no human” harnesses, and not Harness Claw–class personal assistants
- **Tools (hands)** — allowlisted catalog: duties, focus_window, type_text, press_hotkey, backup, search_memory — last gate is the action firewall
- **Working memory** — system/user/observation trail, capped OCR, compact window + playlist state each turn
- **Procedural memory** — taught duties under `storage/duties/` (the workday moat). `search_memory` keyword-searches duties, `storage/agent.md`, and recent audit rows (no vector DB yet)
- **Skills** — taught duties and imported packs under `storage/duties/` (including `packs/`). Skills = workday routines, not pentest modules. Chat `import demo pack` then `run duty demo notepad hello`
- **Evidence** — each agent-loop / playlist run writes a redacted markdown report to `storage/runs/`
- **Local learning** — failures and prefs append uniquely to `storage/agent.md` (Preferences / Lessons / Last-good duties)
- **Resume** — say `resume` to continue the last saved goal (desktop tools still need Approve)
- **Bot-sitter** — Approve UI tags **read** vs **desktop** risk; nothing desktop-destructive runs until you Approve
- **Landmarks** — replay prefers window-title focus (and optional OCR text) before raw coordinates; pauses if missing
- **ToolRouter** — in-process backup/sort dispatcher — **not** MCP process isolation
- **Broker** — optional WebSocket on `127.0.0.1` with token — **off by default**
- **Ledger / sleep-time** — audit rows can feed preferences in `storage/agent.md`

HITL trust patterns (Approve, evidence, local learning, secret redaction) are inspired by analyst-in-the-loop agent tools such as [PentesterFlow](https://cybersecuritynews.com/pentesterflow/) — **adapted for workday desktop automation only**. VassalOps is not a pentest product and has no YOLO auto-approve.

Complementary to chat/gateway harnesses (e.g. OpenClaw) and Buzz-class agent workspaces ([Buzz](https://github.com/block/buzz)): those are team chat plus coding agents. VassalOps is the local Windows workday loop — teach → Approve → run duties. They are not the same product. On-device chat/image apps (phone offline LLMs, LAN model APIs) are complementary too — VassalOps is not a mobile LLM client or LAN model server. [Agent Plugins](https://developers.googleblog.com/agent-plugins-package-your-skills-tools-and-more/) (portable Skills + MCP for coding agents/IDEs) are complementary as well — VassalOps ships workday duty packs under `storage/duties/packs/` with Approve, not an Agent Plugins client or MCP host. [Gemini Spark](https://gemini.google/overview/agent/spark/)–class Workspace agents (cloud Gmail/Calendar automation) are complementary too — VassalOps is not Spark or Antigravity.

---

## Security

Treat every proposed plan as untrusted until you read it. Desktop automation runs **as your Windows user**.

- **Approve required** before teach, fetch, duty run, playlist run, or the agent loop
- Approve UI shows **read** vs **desktop** risk; desktop tools run only after Approve
- **Stuck / MFA pause** — missing window or landmark freezes automation and asks you to Continue (no silent smash-through)
- Dangerous hotkeys (e.g. Alt+F4, Win+L) are denylisted
- **Broker** stays on localhost + shared token when enabled
- **Teach mode** can record keystrokes (including passwords) — prefer click-only for logins; we warn in UI
- **No silent autopilot / no YOLO mode** — morning Task Scheduler only opens the briefing UI

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

### Who buys this / service angle

VassalOps can be sold as a one-time or retainer **workday automation setup** for Windows-using local/SMB operators: map boring, repetitive desktop tasks into taught duties that still require **Approve**. Unlike cloud n8n/webhook bots, it runs on the PC they already use. Proof is the 60-second Notepad demo (`import demo pack` → `run duty demo notepad hello`). Natural wedge buyers are also agencies/consultants already selling into local SMB ops — they resell Approve workday setup, which is distinct from Cloudflare-style pay-per-crawl / agent-web resource businesses ([Startup Ideas on Cloudflare](https://youtu.be/MNNfat_QP0E)). This is not a LinkedIn-ghostwriting, AI-avatar, or content-farm product.

---

## License

MIT — see [LICENSE](LICENSE).
