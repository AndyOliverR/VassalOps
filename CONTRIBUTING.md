# Contributing to VassalOps

Thanks for helping. Keep changes **focused**, **local-first**, and **honest** about what the code actually does. Do not reintroduce LAN-exposed brokers by default or auto-approve desktop macros from chat.

Scope stays **desktop Approve + duties**. Do not PR Buzz, ACP, or a Nostr relay as core product — those belong to complementary agent workspaces, not VassalOps. Do not PR content-farm, LinkedIn-ghostwriting, or AI-avatar features as core product. Do not PR Kiro, Amazon Q, or cloud coding-agent fleets as core product. Do not PR a Flutter/mobile LLM client, on-device image generation, or a LAN-exposed OpenAI-compatible model server as core product. Do not PR Agent Plugins / MCP packaging as core runtime. Do not PR Harness Claw / OpenClaw-clone personal-agent runtimes or unsupervised no-Approve desktop harnesses as core product. Do not PR Cloudflare pay-per-crawl / X402 agent-payment rails, niche web data-refinery products, or agent-readiness SEO SaaS as core product. Do not PR Gemini Spark, Antigravity SDK/CLI, or Gemini Managed Agents as core runtime.

AI-assisted PRs are welcome when hermetic tests pass and README / SECURITY claims stay accurate. Maintainer judgement still decides merge — Copilot or other assistants do not.

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
| `src/execution/agent_loop.py` / `agent_tools.py` | Bounded think-act-observe loop + allowlisted tool catalog + keyword memory |
| `src/execution/structured_llm.py` | Local Pydantic JSON schemas + one validation retry (Instructor-style, not Instructor SaaS) |
| `src/execution/domain_rules.py` | Thin workday domain checks after tools (not OWL/Neo4j) |
| `src/execution/duty_library.py` / `daily_playlist.py` | Teach / list / run duties and workday playlist |
| `src/execution/macro_recorder.py` / `macro_player.py` | Record / replay with landmarks + stuck pause |
| `src/execution/landmark_target.py` | Window focus + optional OCR landmarks |
| `src/execution/run_controller.py` / `plan_narrator.py` | Live progress, Stop, plain-English plans |
| `src/execution/action_firewall.py` | Allowlist for action types |
| `src/execution/tool_router.py` | In-process tools (backup/sort) — not MCP isolation |
| `src/ingestion/secret_redactor.py` | Redact secrets before model prompts |
| `src/communication/socket_broker.py` | Optional localhost broker (token required) |
| `storage/dashboard/` | Control panel UI (Glow Icons subset under `assets/icons/`) |
| `storage/duties/` | Duty JSON + `packs/` demos |
| `SECURITY.md` | Threat model and vulnerability reporting |

---

## Good first issues

Browse Issues labeled **`good first issue`** / **`help wanted`**. High-value starter areas:

1. **Second safe demo duty pack** — done: Calculator pack in `storage/duties/packs/` (see [docs/DEMO.md](docs/DEMO.md)). Extra packs (e.g. Paint) still welcome.
2. **Landmark robustness** — window-title scoring + OCR multi-word join in `landmark_target.py`; extend with more hermetic cases as needed.
3. **Dashboard copy / a11y** — clearer Approve and stuck-panel wording in `storage/dashboard/`.
4. **Docs polish** — demo script in [docs/DEMO.md](docs/DEMO.md); commit a short screen GIF there when you record one.
5. **Theme toggle** — light/dark preference in `localStorage` for the dashboard.
6. **ToolRouter disk-space tool** — safe free-disk check still behind Approve (`tool_router.py`).

If no open issue matches, open one with a clear problem statement before a large PR.

---

## Debugging duties JSON

Duty files live in `storage/duties/` (playlist payloads and Approve JSON can nest several layers). To inspect a file as a graph, paste it into [jsoncrack.com](https://jsoncrack.com) in a browser. That site is not part of VassalOps and is not called at runtime.

Planner and agent-loop replies are validated against local Pydantic schemas in `src/execution/structured_llm.py` (one retry with the validation error). That is Instructor-style structured output, not a dependency on the Instructor product.

---

## Local AI code review

Optional contributor tool — **not** part of the VassalOps runtime, CI, or chat. It does not replace human PR review or the in-app **Approve** gate.

Alibaba’s [Open Code Review](https://github.com/alibaba/open-code-review) (`ocr` CLI, Apache 2.0) reads a Git diff and returns line-level comments. Point it at **local Ollama** so code stays on your machine. The CLI name `ocr` is Open Code Review, not VassalOps screen OCR in `src/ingestion/ocr_reader.py`.

```bash
npm install -g @alibaba-group/open-code-review
ocr config provider
```

Use an OpenAI-compatible endpoint such as `http://127.0.0.1:11434/v1` (Ollama must already be running). Then:

```bash
ocr review
ocr review --from main
```

Reviews surface issues; they do not approve merges. Quality matches the model you configure. VassalOps already uses the same hybrid idea for desktop actions: deterministic firewall and schemas, an LLM plan, then a human Approve.

---

## GitHub security features (maintainers)

These are repo settings, not VassalOps runtime. Enable on [AndyOliverR/VassalOps](https://github.com/AndyOliverR/VassalOps):

- Secret scanning
- Dependabot alerts (pip updates via `.github/dependabot.yml`)
- Private vulnerability reporting (see [SECURITY.md](SECURITY.md))

Do not claim CodeQL, GitHub Advanced Security, or Secure Fund participation unless those are actually enabled.

---

## Workflow

1. Fork and branch: `git checkout -b feature/your-improvement`
2. Make a small, reviewable change
3. Run hermetic tests (command above)
4. Open a PR against `main` with **why**, not only what
5. Link related Issues

### Releases (maintainers)

1. Bump the `VERSION` file (semver, no `v` prefix)
2. Merge to `main`, then tag matching that version: `git tag v0.1.0 && git push origin v0.1.0`
3. `.github/workflows/release.yml` publishes `VassalOps-<VERSION>.zip` on the GitHub Release
4. Launch-time `update_vassalops.ps1` offers that zip to users (never silent; preserves `storage/` + `config.json`)

### PR expectations

- No auto-Approve of desktop macros
- No unsupervised scheduled desktop macros or infinite outer loops that bypass Approve
- No overnight unsupervised duty-mutation / auto-research loops that bypass Approve or rewrite success metrics
- Broker remains localhost + token when touched
- Do not claim OS sandbox / MCP isolation / unsupervised “become me” in docs
- Do not add Buzz / ACP / Nostr relay as a runtime dependency or chat command
- Do not add content-farm, LinkedIn-ghostwriting, or AI-avatar features as core product
- Do not add Kiro / Amazon Q / cloud coding-agent fleets as core product
- Do not add unattended multi-hour desktop agent fleets that skip Approve
- Do not add a Flutter/mobile LLM client, on-device image generation, or a LAN-exposed OpenAI-compatible model server as core product
- Do not add Agent Plugins / MCP packaging as core runtime
- Do not add Harness Claw / OpenClaw-clone personal-agent runtimes or unsupervised no-Approve desktop harnesses as core product
- Do not add Cloudflare pay-per-crawl / X402 agent-payment rails, niche web data-refinery products, or agent-readiness SEO SaaS as core product
- Do not add Gemini Spark, Antigravity SDK/CLI, or Gemini Managed Agents as core runtime
- Prefer new tests for duty/playlist/firewall/landmark behavior

---

## Code of conduct (short)

Be respectful. Assume good faith. Security reports go through [SECURITY.md](SECURITY.md), not public issues when disclosure could harm users.
