"""Allowlisted tool catalog and keyword memory search for the agent loop."""

from __future__ import annotations

import os
import re
from typing import Any, Callable, Dict, List, Optional


TOOL_CATALOG: List[Dict[str, str]] = [
    {"name": "list_duties", "description": "List taught daily duties (ids, names, step counts). Payload ignored."},
    {"name": "run_duty", "description": "Replay one taught duty by id or name.", "payload": "duty id or name"},
    {"name": "focus_window", "description": "Bring a window to the foreground by title substring.", "payload": "window title substring"},
    {"name": "type_text", "description": "Type text into the focused window (no Enter).", "payload": "text to type"},
    {"name": "press_hotkey", "description": "Press a hotkey combo such as ctrl+s or win+r.", "payload": "keys joined by +"},
    {"name": "speak_log", "description": "Record a short status note for the user (no desktop action).", "payload": "message"},
    {"name": "run_backup", "description": "Run the local backup tool.", "payload": "empty"},
    {"name": "search_memory", "description": "Keyword-search duties, agent.md preferences, and recent audit rows.", "payload": "search query"},
]

LOOP_TOOL_NAMES = {t["name"] for t in TOOL_CATALOG}

MAX_OCR_CHARS = 1200
MAX_TRAIL_CHARS = 8000


def catalog_prompt_block() -> str:
    lines = ["Allowed tools (name — description):"]
    for tool in TOOL_CATALOG:
        extra = f" Payload: {tool['payload']}." if tool.get("payload") else ""
        lines.append(f"- {tool['name']}: {tool['description']}{extra}")
    return "\n".join(lines)


def cap_ocr(text: str, limit: int = MAX_OCR_CHARS) -> str:
    raw = (text or "").strip()
    if len(raw) <= limit:
        return raw
    return raw[: limit - 18] + "\n...[ocr truncated]"


def truncate_messages(messages: List[Dict[str, str]], max_chars: int = MAX_TRAIL_CHARS) -> List[Dict[str, str]]:
    """Keep system + first user + newest turns so the context window stays bounded."""
    if not messages:
        return []
    head: List[Dict[str, str]] = []
    idx = 0
    if messages[0].get("role") == "system":
        head.append(messages[0])
        idx = 1
    if idx < len(messages) and messages[idx].get("role") == "user":
        head.append(messages[idx])
        idx += 1
    trail = messages[idx:]
    kept: List[Dict[str, str]] = []
    budget = max_chars
    for msg in reversed(trail):
        size = len(msg.get("content") or "") + 16
        if kept and budget - size < 0:
            kept.append({"role": "observation", "content": "[older turns summarized: dropped to fit context]"})
            break
        kept.append(msg)
        budget -= size
    kept.reverse()
    return head + kept


def render_messages(messages: List[Dict[str, str]]) -> str:
    chunks = []
    for msg in messages:
        role = (msg.get("role") or "assistant").upper()
        chunks.append(f"{role}: {msg.get('content') or ''}")
    return "\n\n".join(chunks)


def compact_workspace_state(
    *,
    window_titles: Optional[List[str]] = None,
    playlist_items: Optional[List[Dict[str, Any]]] = None,
    last_error: str = "",
) -> str:
    titles = [t for t in (window_titles or []) if t][:8]
    due = []
    for item in playlist_items or []:
        if item.get("due") and item.get("exists"):
            due.append(str(item.get("name") or item.get("duty_id")))
    lines = [
        f"Open windows: {', '.join(titles) if titles else '(none listed)'}",
        f"Due playlist duties: {', '.join(due) if due else '(none due)'}",
        f"Last error: {last_error or '(none)'}",
    ]
    return "\n".join(lines)


def search_memory(
    query: str,
    *,
    duty_library=None,
    ledger=None,
    agent_md_path: str = os.path.join("storage", "agent.md"),
    limit: int = 8,
) -> str:
    """Keyword retrieval over duties, agent.md, and recent audit intents (no vector DB)."""
    needle = (query or "").strip().lower()
    if not needle:
        return "search_memory: empty query."
    tokens = [t for t in re.split(r"\W+", needle) if t]
    hits: List[str] = []

    if duty_library is not None:
        try:
            for duty in duty_library.list_duties():
                blob = " ".join(
                    str(duty.get(k) or "") for k in ("id", "name", "description")
                ).lower()
                if any(tok in blob for tok in tokens):
                    hits.append(
                        f"duty {duty.get('id')}: {duty.get('name')} "
                        f"({duty.get('step_count', 0)} steps, last {duty.get('last_run') or 'never'})"
                    )
        except Exception as exc:
            hits.append(f"duties search error: {exc}")

    if os.path.isfile(agent_md_path):
        try:
            with open(agent_md_path, "r", encoding="utf-8") as f:
                text = f.read()
            for line in text.splitlines():
                low = line.lower()
                if line.strip() and any(tok in low for tok in tokens):
                    hits.append(f"agent.md: {line.strip()[:200]}")
                    if len(hits) >= limit:
                        break
        except Exception as exc:
            hits.append(f"agent.md error: {exc}")

    if ledger is not None and len(hits) < limit:
        try:
            for row in ledger.fetch_recent_intents(limit=20):
                blob = f"{row.get('command_intent')} {row.get('execution_status')}".lower()
                if any(tok in blob for tok in tokens):
                    hits.append(
                        f"audit: {row.get('command_intent')} [{row.get('execution_status')}]"
                    )
                if len(hits) >= limit:
                    break
        except Exception as exc:
            hits.append(f"ledger search error: {exc}")

    if not hits:
        return f"search_memory: no matches for '{query}'."
    return "search_memory hits:\n- " + "\n- ".join(hits[:limit])


def execute_loop_tool(
    name: str,
    payload: str,
    *,
    duty_library=None,
    daily_playlist=None,
    operator_bridge=None,
    tool_router=None,
    run_controller=None,
    press_hotkey: Optional[Callable[[str], None]] = None,
    type_text: Optional[Callable[[str], None]] = None,
    focus_window: Optional[Callable[[str], Dict[str, Any]]] = None,
    ledger=None,
    agent_md_path: str = os.path.join("storage", "agent.md"),
) -> Dict[str, Any]:
    """Run one allowlisted loop tool. Returns {ok, observation}."""
    tool = (name or "").strip()
    arg = payload if payload is not None else ""
    if tool not in LOOP_TOOL_NAMES:
        return {"ok": False, "observation": f"Rejected unknown tool '{tool}'."}

    try:
        if tool == "list_duties":
            if duty_library is None:
                return {"ok": False, "observation": "Duty library unavailable."}
            text = duty_library.format_duty_list()
            return {"ok": True, "observation": text}

        if tool == "run_duty":
            if duty_library is None:
                return {"ok": False, "observation": "Duty library unavailable."}
            from src.execution.duty_library import _slugify
            outcome = duty_library.run_duty(_slugify(str(arg)))
            ok = bool(outcome.get("ok"))
            return {"ok": ok, "observation": str(outcome)}

        if tool == "focus_window":
            if focus_window is None:
                return {"ok": False, "observation": "focus_window helper unavailable."}
            result = focus_window(str(arg))
            if result.get("ok"):
                return {"ok": True, "observation": f"Focused window matching '{arg}'."}
            if run_controller is not None:
                run_controller.enter_stuck(
                    result.get("error") or f"Window “{arg}” not found.",
                    "Open the window, then Continue in VassalOps.",
                )
                decision = run_controller.wait_while_paused()
                if decision == "stop":
                    return {"ok": False, "observation": "Stopped while waiting for window.", "stop": True}
                if decision == "skip":
                    return {"ok": True, "observation": f"Skipped focus_window '{arg}'."}
                retry = focus_window(str(arg))
                if retry.get("ok"):
                    return {"ok": True, "observation": f"Focused window matching '{arg}' after Continue."}
            return {"ok": False, "observation": result.get("error") or f"Window '{arg}' not found."}

        if tool == "type_text":
            if type_text is None:
                return {"ok": False, "observation": "type_text helper unavailable."}
            type_text(str(arg))
            return {"ok": True, "observation": f"Typed {len(str(arg))} characters."}

        if tool == "press_hotkey":
            if press_hotkey is None:
                return {"ok": False, "observation": "press_hotkey helper unavailable."}
            press_hotkey(str(arg))
            return {"ok": True, "observation": f"Pressed hotkey {arg}."}

        if tool == "speak_log":
            return {"ok": True, "observation": str(arg)}

        if tool == "run_backup":
            if tool_router is None:
                return {"ok": False, "observation": "ToolRouter unavailable."}
            result = tool_router.call_tool("run_backup")
            return {"ok": result.get("status") == "success", "observation": result.get("message") or str(result)}

        if tool == "search_memory":
            text = search_memory(
                str(arg),
                duty_library=duty_library,
                ledger=ledger,
                agent_md_path=agent_md_path,
            )
            return {"ok": True, "observation": text}
    except Exception as exc:
        return {"ok": False, "observation": f"Tool '{tool}' failed: {exc}"}

    return {"ok": False, "observation": f"Tool '{tool}' not executed."}
