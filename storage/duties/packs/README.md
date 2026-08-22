# Workday skill packs

**Skills = taught or imported duties** — safe, password-free workday routines. Not pentest / vuln packs. Packs are VassalOps’s “travel together” unit for those routines (same packaging instinct as [Agent Plugins](https://developers.googleblog.com/agent-plugins-package-your-skills-tools-and-more/)), still duty JSON + Approve — not the Agent Plugins `plugin.json` / `mcp.json` directory format.

Import with chat: `import demo pack` then `run duty <id>` after **Approve**. Full script: [docs/DEMO.md](../../../docs/DEMO.md).

## ICM staged packs (folder stages + human gates)

Inspired by folder-as-architecture (ICM): each stage is a folder with `CONTEXT.md` (Input → Process → Output → Stop-for-Approve) plus `duty.json` and optional `output/` handoffs. **Stages decide where the human sits** — not silent overnight desktop, and **not** a cloud multi-agent “Slack” of bots (Grockbot-style teams stay out of scope).

Sample: [`staged_demo_notepad/`](staged_demo_notepad/)

1. `import demo pack`
2. `run staged pack staged demo notepad` (or `run duty staged demo notepad`) → **Approve**
3. Stage 1 opens Notepad → progress panel **Needs you** + second **Approve** to continue
4. Stage 2 types the greeting → done

Author new staged packs the same way: `pack.json` + numbered stage folders under `storage/duties/packs/<name>/`.

## Morning Notepad Briefing (demo skill)

Goal: prove “type it / teach it → PC does it” in ~60 seconds without Outlook/SAP credentials.

1. Install & open VassalOps (`install_vassalops.ps1` once, then Desktop shortcut).
2. Chat: `import demo pack`
3. Chat: `run duty demo notepad hello` → **Approve**
4. Watch the progress panel (Stop / Continue if stuck). A redacted report lands in `storage/runs/`.
5. Or teach your own skill: `teach morning email` → do the real task → Escape → `build my workday`.

## Calculator 1+1 (second demo skill)

Password-free alternate proof: opens Calculator via Win+R and types `1+1=`.

1. Chat: `import demo pack`
2. Chat: `run duty demo calculator one plus one` → **Approve**
3. Watch Calculator; Stop / Continue if the window title does not match.

Flat JSON files in this folder are copied into `storage/duties/` on import. Staged pack folders import each stage `duty.json` the same way. The agent loop can `list_duties` / `search_memory` / `run_duty` to discover them.

When authoring or teaching a duty, state what **success** looks like (e.g. in `description` or the teach brief) so a human can score a run against `storage/runs/` evidence. The agent must not rewrite that success definition to “pass” itself.

**Marketing spine:** *Your PC’s workday — taught by you, approved by you, run locally.*
