"""Structured local learning into agent.md with line-level dedupe."""

from __future__ import annotations

import os
from typing import Iterable, List

from src.execution.diagnostics_engine import ensure_agent_memory_file
from src.ingestion.secret_redactor import redact_secrets


SECTIONS = ("## Preferences", "## Lessons", "## Last-good duties")


def _ensure_sections(text: str) -> str:
    out = text.rstrip() + "\n"
    for heading in SECTIONS:
        if heading not in out:
            out += f"\n{heading}\n"
    return out


def _existing_bullets(text: str) -> set:
    return {line.strip() for line in text.splitlines() if line.strip().startswith("- ")}


def append_unique_bullets(memory_path: str, section: str, bullets: Iterable[str]) -> int:
    """Append unique `- ` lines under a markdown section. Returns how many were added."""
    ensure_agent_memory_file(memory_path)
    with open(memory_path, "r", encoding="utf-8") as f:
        text = f.read()
    text = _ensure_sections(text)
    seen = _existing_bullets(text)
    added: List[str] = []
    for raw in bullets:
        line = "- " + redact_secrets((raw or "").strip()).lstrip("- ").strip()
        if len(line) < 5 or line in seen:
            continue
        seen.add(line)
        added.append(line)
    if not added:
        with open(memory_path, "w", encoding="utf-8") as f:
            f.write(text if text.endswith("\n") else text + "\n")
        return 0
    heading = section if section.startswith("## ") else f"## {section}"
    start = text.find(heading)
    if start < 0:
        text += f"\n{heading}\n" + "\n".join(added) + "\n"
    else:
        rest = text[start + len(heading):]
        nxt = rest.find("\n## ")
        if nxt < 0:
            text = text.rstrip() + "\n" + "\n".join(added) + "\n"
        else:
            abs_nxt = start + len(heading) + nxt
            text = text[:abs_nxt].rstrip() + "\n" + "\n".join(added) + "\n" + text[abs_nxt:]
    with open(memory_path, "w", encoding="utf-8") as f:
        f.write(text)
    return len(added)


def record_loop_outcome(memory_path: str, report: dict, goal: str = "") -> int:
    """Write prefs/lessons from an agent-loop or playlist report."""
    added = 0
    observations = report.get("observations") or []
    if not report.get("ok"):
        reason = report.get("reason") or "failed"
        if "window" in reason.lower() or any("window" in str(o).lower() for o in observations):
            added += append_unique_bullets(
                memory_path,
                "## Preferences",
                ["skip if window missing: pause and ask human (do not smash clicks)"],
            )
        if "fail" in reason.lower() or not report.get("ok"):
            added += append_unique_bullets(
                memory_path,
                "## Lessons",
                [f"failed: {reason[:160]} (goal: {(goal or '')[:80]})"],
            )
    else:
        added += append_unique_bullets(
            memory_path,
            "## Last-good duties",
            [f"ok: {(goal or 'run')[:80]} in {report.get('turns', 0)} turns"],
        )
    return added
