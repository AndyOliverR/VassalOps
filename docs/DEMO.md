# 60-second demo (record a GIF from this path)

VassalOps stands out when someone **sees** teach → Approve → run. Use either demo pack below, then optionally capture a short screen GIF for the README.

## Prerequisites

- VassalOps open (`bootstrap_and_run.bat` or Desktop shortcut)
- Ollama running (bootstrap usually starts it)

## Path A — Notepad hello

1. Chat: `import demo pack`
2. Chat: `run duty demo notepad hello`
3. Read the plain-English plan → **Approve**
4. Watch Notepad open and type the greeting (use **Stop** or **Continue** if stuck)

## Path B — Calculator 1+1

1. Chat: `import demo pack` (imports both packs)
2. Chat: `run duty demo calculator one plus one`
3. **Approve** → Calculator should open and type `1+1=`

## Capture a GIF for docs / README

1. Use Windows Game Bar (`Win+G`) or any screen recorder.
2. Record only Path A or B (about 15–30 seconds).
3. Save as `docs/demo-notepad.gif` (or `docs/demo-calculator.gif`).
4. Link it from [README.md](../README.md) Quick start when the file exists.

Until a GIF is committed, this markdown is the canonical demo script.

## Path C — Staged ICM pack (Approve between stages)

Folder-as-architecture demo (not a multi-agent swarm):

1. Chat: `import demo pack`
2. Chat: `run staged pack staged demo notepad`
3. **Approve** → stage 1 opens Notepad
4. Progress panel shows **Needs you** + **Approve replan / continue** → stage 2 types the greeting
5. Optional: edit `storage/duties/packs/staged_demo_notepad/01_open_notepad/output/handoff.md` before the second Approve

Stages decide where the human sits. Silent overnight desktop and cloud “agent Slack” teams are out of scope.

## Path D — Sugar / Spice / Element X (robustness)

After a successful Approve run, VassalOps stores a **Duty Reflex** under `storage/reflexes/` (window titles / landmarks that worked). The next similar goal injects that context — still **Approve before desktop**.

During a run, watch the progress panel:

- Live **checklist** (pending / running / done)
- Plain-English **summary** when stuck or finished
- Auto-retry before Pause (refocus window / re-OCR), then Continue / Skip / **Approve replan**

Workspace coding-lite tools (`list_dir`, `read_file`, hermetic `run_unittest`) stay inside the VassalOps folder; `write_file` only after Approve.

1. `teach morning email` → Approve → do the task → Escape  
2. `build my workday`  
3. **Daily Duties** → **Approve today's run**
