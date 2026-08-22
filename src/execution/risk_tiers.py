"""Classify proposed actions as read-only vs desktop-write for Approve UI."""

from __future__ import annotations

from typing import Any, Dict, List


READ_TYPES = {
    "speak_log",
    "list_duties",
    "search_memory",
    "extract_intel",
}

DESKTOP_TYPES = {
    "type_text",
    "press_key",
    "press_hotkey",
    "click_element",
    "click_landmark",
    "focus_window",
    "run_duty",
    "run_staged_pack",
    "run_playlist",
    "run_saved_macro",
    "learn_macro",
    "teach_duty",
    "run_backup",
    "sort_intel",
    "agent_loop",
}


def tool_risk(action_type: str) -> str:
    name = (action_type or "").strip()
    if name in READ_TYPES:
        return "read"
    if name in DESKTOP_TYPES:
        return "desktop"
    return "desktop"


def annotate_steps(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for step in steps or []:
        if not isinstance(step, dict):
            continue
        item = dict(step)
        item["risk"] = tool_risk(str(step.get("type") or ""))
        out.append(item)
    return out


def risk_summary(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    annotated = annotate_steps(steps)
    has_desktop = any(s.get("risk") == "desktop" for s in annotated)
    has_read = any(s.get("risk") == "read" for s in annotated)
    return {
        "has_desktop": has_desktop,
        "has_read": has_read,
        "desktop_count": sum(1 for s in annotated if s.get("risk") == "desktop"),
        "read_count": sum(1 for s in annotated if s.get("risk") == "read"),
        "message": (
            "Desktop tools will run only after Approve."
            if has_desktop
            else "Read-only tools only — still review before Approve."
        ),
    }
