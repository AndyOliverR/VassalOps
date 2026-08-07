# Contributing to VassalOps

Thanks for helping improve VassalOps. Keep changes focused, local-first, and honest about what the code actually does.

---

## Project map

- `app.py` — LangGraph entry, pywebview `js_api` (`submit_command` / `confirm_plan`), macro execution
- `src/execution/tool_router.py` — In-process tool dispatcher (backup/sort); not MCP isolation
- `src/execution/diagnostics_engine.py` — Screener / Verifier / Director over audit ledger traces
- `src/execution/action_firewall.py` — Allowlist for executable action types
- `src/ingestion/secret_redactor.py` — Redacts secrets before model prompts
- `src/communication/socket_broker.py` — Optional localhost WebSocket broker (token required)
- `storage/dashboard/` — HTML/CSS/JS control panel
- `storage/agent.md` — Long-term preference notes updated by sleep-time compute

---

## Good first issues

### 1. Expand IssueBench synthetic tasks

- **File:** `src/execution/issue_bench.py`
- Add a few mock error profiles for verifier stress tests.

### 2. Theme toggle in the dashboard

- **File:** `storage/dashboard/index.html` (+ CSS/JS)
- Persist light/dark preference in `localStorage`.

### 3. Add a disk-space tool to ToolRouter

- **File:** `src/execution/tool_router.py`
- Expose a safe free-disk check as a listed tool the planner can propose (still subject to human approval).

---

## Workflow

1. Fork and branch: `git checkout -b feature/your-improvement`
2. Install deps: `pip install -r requirements.txt`
3. Run hermetic tests: `python -m unittest discover -s tests -p "test_*.py"`
4. Live Ollama/network checks only when needed: set `VASSALOPS_LIVE=1`
5. Open a PR against `main` with a short description of why

We prefer small PRs that do not reintroduce LAN-exposed brokers by default or auto-approve desktop macros from chat.
