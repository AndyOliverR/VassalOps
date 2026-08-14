"""Thin workday domain rules — neuro-symbolic lite, not OWL/Neo4j.

Shared conceptualization for the agent loop: Duty, Playlist, Window, Risk.
Pydantic validates JSON at the door; these rules check tool results at the ledger.
They do not replace the action firewall or the human Approve gate.
"""

from __future__ import annotations

from typing import Any, Dict

from src.execution.agent_tools import LOOP_TOOL_NAMES

WORKDAY_ENTITIES = ("Duty", "Playlist", "Window", "Risk")

READ_TOOLS = frozenset({"list_duties", "search_memory", "speak_log", "run_backup"})
DESKTOP_TOOLS = frozenset({"run_duty", "focus_window", "type_text", "press_hotkey"})

_SHELLISH = ("shell_", "cmd_", "powershell", "bash_", "os.system")


def domain_prompt_block() -> str:
    """One paragraph the model sees as the shared workday conceptualization."""
    return (
        "WORKDAY DOMAIN (entities: Duty, Playlist, Window, Risk read/desktop). "
        "Only allowlisted tools. Never invent shell_* or unrestricted command tools. "
        "run_duty requires a taught Duty. focus_window requires a real Window title. "
        "Domain notes after a tool are constraints — they do not replace human Approve."
    )


def check_tool_result(name: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """Return {ok, note} for simple workday invariants. Empty note means no extra signal."""
    tool = (name or "").strip()
    obs = str((result or {}).get("observation") or "")
    obs_l = obs.lower()
    result_ok = bool((result or {}).get("ok"))

    low = tool.lower()
    if any(low.startswith(p) or low == p.rstrip("_") for p in _SHELLISH):
        return {
            "ok": False,
            "note": "Domain: never invent shell_* tools. Use allowlisted Duty/Window tools only.",
        }

    if tool not in LOOP_TOOL_NAMES:
        return {
            "ok": False,
            "note": f"Domain: '{tool}' is not a workday tool (Duty, Playlist, Window, Risk catalog).",
        }

    if tool == "focus_window" and not result_ok:
        if "not found" in obs_l or "unavailable" in obs_l:
            return {
                "ok": False,
                "note": "Domain: Window entity missing — open the window or use a listed title, then retry.",
            }

    if tool == "run_duty" and not result_ok:
        if any(k in obs_l for k in ("not found", "missing", "unknown duty", "no such")):
            return {
                "ok": False,
                "note": "Domain: run_duty needs a taught Duty id. Use list_duties first.",
            }

    if tool == "list_duties" and result_ok:
        if "no duties" in obs_l or obs.strip() in ("", "[]"):
            return {
                "ok": True,
                "note": "Domain: Playlist/Duty set is empty — teach a duty before run_duty.",
            }

    return {"ok": True, "note": ""}
