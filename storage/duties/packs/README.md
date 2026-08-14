# Workday skill packs

**Skills = taught or imported duties** — safe, password-free workday routines. Not pentest / vuln packs. Packs are VassalOps’s “travel together” unit for those routines (same packaging instinct as [Agent Plugins](https://developers.googleblog.com/agent-plugins-package-your-skills-tools-and-more/)), still duty JSON + Approve — not the Agent Plugins `plugin.json` / `mcp.json` directory format.

Import with chat: `import demo pack` then `run duty <id>` after **Approve**.

## Morning Notepad Briefing (demo skill)

Goal: prove “type it / teach it → PC does it” in ~60 seconds without Outlook/SAP credentials.

1. Install & open VassalOps (`install_vassalops.ps1` once, then Desktop shortcut).
2. Chat: `import demo pack`
3. Chat: `run duty demo notepad hello` → **Approve**
4. Watch the progress panel (Stop / Continue if stuck). A redacted report lands in `storage/runs/`.
5. Or teach your own skill: `teach morning email` → do the real task → Escape → `build my workday`.

JSON files in this folder are copied into `storage/duties/` on import. The agent loop can `list_duties` / `search_memory` / `run_duty` to discover them.

When authoring or teaching a duty, state what **success** looks like (e.g. in `description` or the teach brief) so a human can score a run against `storage/runs/` evidence. The agent must not rewrite that success definition to “pass” itself.

**Marketing spine:** *Your PC’s workday — taught by you, approved by you, run locally.*