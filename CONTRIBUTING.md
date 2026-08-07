# Contributing to VassalOps

Thanks for helping. Keep changes **focused**, **local-first**, and **honest** about what the code actually does. Do not reintroduce LAN-exposed brokers by default or auto-approve desktop macros from chat.

AI-assisted PRs are welcome when hermetic tests pass and README / SECURITY claims stay accurate.

---

## Setup

```bash
git clone https://github.com/AndyOliverR/VassalOps.git
cd VassalOps
pip install -r requirements.txt
```

On Windows PowerShell for tests:

```powershell
$env:PYTHONPATH = (Get-Location).Path
python -m unittest discover -s tests -p "test_*.py"
```

Live Ollama/network checks only when needed: set `VASSALOPS_LIVE=1`.

Run the UI: `python app.py` or `bootstrap_and_run.bat`.

---

## Project map

| Path | Role |
|------|------|
| `app.py` | LangGraph entry, pywebview `js_api`, Approve execution |
| `src/execution/duty_library.py` / `daily_playlist.py` | Teach / list / run duties and workday playlist |
| `src/execution/macro_recorder.py` / `macro_player.py` | Record / replay with landmarks + stuck pause |
| `src/execution/landmark_target.py` | Window focus + optional OCR landmarks |
| `src/execution/run_controller.py` / `plan_narrator.py` | Live progress, Stop, plain-English plans |
| `src/execution/action_firewall.py` | Allowlist for action types |
| `src/execution/tool_router.py` | In-process tools (backup/sort) — not MCP isolation |
| `src/ingestion/secret_redactor.py` | Redact secrets before model prompts |
| `src/communication/socket_broker.py` | Optional localhost broker (token required) |
| `storage/dashboard/` | Control panel UI |
| `storage/duties/` | Duty JSON + `packs/` demos |
| `SECURITY.md` | Threat model and vulnerability reporting |

---

## Good first issues

Browse Issues labeled **`good first issue`** / **`help wanted`**. High-value starter areas:

1. **Second safe demo duty pack** — `storage/duties/packs/` (no passwords; e.g. Calculator or Paint).
2. **Landmark robustness** — better window-title matching or OCR fallbacks in `landmark_target.py` + tests.
3. **Dashboard copy / a11y** — clearer Approve and stuck-panel wording in `storage/dashboard/`.
4. **Docs polish** — typos, screenshots, or a short GIF of the Notepad demo linked from README.
5. **Theme toggle** — light/dark preference in `localStorage` for the dashboard.
6. **ToolRouter disk-space tool** — safe free-disk check still behind Approve (`tool_router.py`).

If no open issue matches, open one with a clear problem statement before a large PR.

---

## Workflow

1. Fork and branch: `git checkout -b feature/your-improvement`
2. Make a small, reviewable change
3. Run hermetic tests (command above)
4. Open a PR against `main` with **why**, not only what
5. Link related Issues

### PR expectations

- No auto-Approve of desktop macros
- Broker remains localhost + token when touched
- Do not claim OS sandbox / MCP isolation / unsupervised “become me” in docs
- Prefer new tests for duty/playlist/firewall/landmark behavior

---

## Code of conduct (short)

Be respectful. Assume good faith. Security reports go through [SECURITY.md](SECURITY.md), not public issues when disclosure could harm users.
