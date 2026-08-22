"""Turn structured action / macro steps into plain-English checklist lines."""

from __future__ import annotations

from typing import Any, Dict, List


ACTION_LABELS = {
    "speak_log": "Say / explain",
    "type_text": "Type text",
    "press_key": "Press key",
    "press_hotkey": "Press hotkey",
    "click_element": "Click UI element",
    "learn_macro": "Record macro",
    "run_saved_macro": "Replay macro",
    "teach_duty": "Teach duty (record)",
    "run_duty": "Run duty",
    "run_staged_pack": "Run staged pack (Approve between stages)",
    "run_playlist": "Run today's workday playlist",
    "run_backup": "Run backup tool",
    "sort_intel": "Sort intel folder",
    "extract_intel": "Extract entities",
    "focus_window": "Focus window",
    "click_landmark": "Click on-screen landmark",
    "agent_loop": "Run bounded agent loop",
    "search_memory": "Search duties / notes / audit",
    "list_duties": "List taught duties",
}


def narrate_action_step(step: Dict[str, Any], index: int = 1) -> str:
    action = str(step.get("type") or "unknown")
    payload = step.get("payload", "")
    label = ACTION_LABELS.get(action, action.replace("_", " "))
    payload_s = str(payload).strip()
    if action == "speak_log" and payload_s:
        # Prefer the human message itself for speak_log
        short = payload_s if len(payload_s) <= 120 else payload_s[:117] + "..."
        return f"{index}. {short}"
    if payload_s:
        return f"{index}. {label}: {payload_s}"
    return f"{index}. {label}"


def narrate_proposed_actions(steps: List[Dict[str, Any]]) -> List[str]:
    return [narrate_action_step(step, i) for i, step in enumerate(steps or [], 1)]


def narrate_macro_step(step: Dict[str, Any], index: int = 1) -> str:
    action = str(step.get("type") or "unknown")
    if action == "click":
        title = (step.get("window_title") or "").strip()
        landmark = (step.get("landmark_text") or "").strip()
        if landmark:
            return f"{index}. Click on-screen text “{landmark}”"
        if title:
            return f"{index}. Click in window “{title}” at ({step.get('x')}, {step.get('y')})"
        return f"{index}. Click at ({step.get('x')}, {step.get('y')})"
    if action == "keystroke":
        return f"{index}. Press key “{step.get('key')}”"
    if action == "hotkey":
        keys = step.get("keys") or step.get("key") or ""
        if isinstance(keys, list):
            keys = "+".join(str(k) for k in keys)
        return f"{index}. Press hotkey {keys}"
    if action == "type_text":
        text = str(step.get("text") or step.get("payload") or "")
        short = text if len(text) <= 40 else text[:37] + "..."
        return f"{index}. Type “{short}”"
    if action == "focus_window":
        return f"{index}. Focus window “{step.get('title') or step.get('payload')}”"
    if action == "wait":
        return f"{index}. Wait {step.get('seconds', 1)}s"
    return f"{index}. {action}"


def narrate_macro_steps(steps: List[Dict[str, Any]]) -> List[str]:
    return [narrate_macro_step(step, i) for i, step in enumerate(steps or [], 1)]
