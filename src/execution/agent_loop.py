"""Bounded think-act-observe loop: LLM chooses a tool, harness runs it, result goes back in."""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional

from src.execution.agent_tools import (
    catalog_prompt_block,
    cap_ocr,
    compact_workspace_state,
    render_messages,
    truncate_messages,
)
from src.execution.domain_rules import check_tool_result, domain_prompt_block
from src.execution.structured_llm import LoopDecisionModel, complete_structured, coerce_json
from src.ingestion.secret_redactor import redact_secrets


SYSTEM_PROMPT = (
    "You are VassalOps, a Windows desktop agent. "
    "An agent is an LLM that uses tools in a loop until the job is done — not a magical brain. "
    "The human already Approved this goal. Desktop tools stay allowlisted. "
    "Treat the user goal as the mission. Infer clear done criteria (what 'finished' looks like). "
    "Work the inner loop: try one tool, observe, then continue or self-correct. "
    "Stay within the turn budget; do not stall. "
    "Return ONLY JSON with one of:\n"
    '{"action":"tool_call","name":"<tool>","payload":"<string>"}\n'
    '{"action":"final","payload":"<short message for the user>"}\n'
    "Use one tool per turn. Prefer list_duties / search_memory / run_duty before guessing clicks. "
    "Do not invent tool names. Use final only when the goal is met or you are blocked; if blocked, say so in final.\n"
    f"{domain_prompt_block()}\n"
    f"{catalog_prompt_block()}"
)


def parse_loop_decision(raw: Any) -> Dict[str, Any]:
    """Normalize model JSON into tool_call | final | invalid via LoopDecisionModel."""
    if isinstance(raw, str):
        text = raw.strip()
        try:
            data = coerce_json(text)
        except Exception:
            return {"kind": "invalid", "error": "Model output was not JSON.", "raw": text[:400]}
    else:
        data = raw
    try:
        decision = LoopDecisionModel.model_validate(data)
    except Exception as exc:
        return {"kind": "invalid", "error": str(exc), "raw": str(raw)[:400]}
    if decision.kind == "final":
        return {"kind": "final", "payload": decision.payload}
    return {"kind": "tool_call", "name": decision.name, "payload": decision.payload}


def build_turn_prompt(messages: List[Dict[str, str]], workspace: str, ocr: str) -> str:
    trail = render_messages(truncate_messages(messages))
    ocr_block = cap_ocr(redact_secrets(ocr or ""))
    return (
        f"{trail}\n\n"
        f"WORKSPACE STATE:\n{workspace}\n\n"
        f"SCREEN OCR (capped, redacted):\n{ocr_block or '(empty)'}\n\n"
        "Reply with JSON only."
    )


def run_agent_loop(
    goal: str,
    *,
    call_model: Callable[[str], Any],
    execute_tool: Callable[[str, str], Dict[str, Any]],
    max_turns: int = 8,
    ocr_text: str = "",
    window_titles: Optional[List[str]] = None,
    playlist_items: Optional[List[Dict[str, Any]]] = None,
    stop_requested: Optional[Callable[[], bool]] = None,
    set_progress: Optional[Callable[[int, str], None]] = None,
) -> Dict[str, Any]:
    """
    Think -> act -> observe until final, max turns, Stop, or a tool requests stop.
    """
    goal_s = redact_secrets((goal or "").strip()) or "(empty goal)"
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Goal (already Approved): {goal_s}"},
    ]
    last_error = ""
    observations: List[str] = []
    turns_used = 0

    for turn in range(1, max_turns + 1):
        turns_used = turn
        if stop_requested and stop_requested():
            return {
                "ok": False,
                "stopped": True,
                "reason": "Stopped by user.",
                "turns": turns_used - 1,
                "final": "",
                "observations": observations,
            }

        workspace = compact_workspace_state(
            window_titles=window_titles,
            playlist_items=playlist_items,
            last_error=last_error,
        )
        prompt = build_turn_prompt(messages, workspace, ocr_text)
        if set_progress:
            set_progress(turn, f"Turn {turn}/{max_turns}: thinking…")

        try:
            structured = complete_structured(prompt, LoopDecisionModel, call_model, max_retries=1)
        except Exception as exc:
            last_error = str(exc)
            return {
                "ok": False,
                "stopped": False,
                "reason": f"Model call failed: {exc}",
                "turns": turns_used,
                "final": "",
                "observations": observations,
            }

        if not structured.ok:
            if (structured.error or "").startswith("Model call failed"):
                last_error = structured.error
                return {
                    "ok": False,
                    "stopped": False,
                    "reason": structured.error,
                    "turns": turns_used,
                    "final": "",
                    "observations": observations,
                }
            last_error = structured.error or "invalid"
            messages.append(
                {
                    "role": "observation",
                    "content": f"Invalid model JSON: {last_error}. Reply with tool_call or final JSON.",
                }
            )
            observations.append(f"turn {turn}: invalid JSON")
            continue

        decision = parse_loop_decision(structured.data.model_dump())
        if decision["kind"] == "invalid":
            last_error = decision.get("error") or "invalid"
            messages.append({"role": "observation", "content": f"Invalid model JSON: {last_error}. Reply with tool_call or final JSON."})
            observations.append(f"turn {turn}: invalid JSON")
            continue

        if decision["kind"] == "final":
            text = decision.get("payload") or "Done."
            if set_progress:
                set_progress(turn, f"Turn {turn}/{max_turns}: finished")
            return {
                "ok": True,
                "stopped": False,
                "reason": "final",
                "turns": turns_used,
                "final": text,
                "observations": observations,
            }

        name = decision["name"]
        payload = decision.get("payload") or ""
        if set_progress:
            set_progress(turn, f"Turn {turn}/{max_turns}: {name}")
        messages.append({"role": "assistant", "content": json.dumps({"action": "tool_call", "name": name, "payload": payload})})

        result = execute_tool(name, payload)
        obs = result.get("observation") or str(result)
        domain = check_tool_result(name, result)
        note = (domain.get("note") or "").strip()
        if note:
            obs = f"{obs}\n{note}"
        observations.append(f"{name}: {obs}")
        last_error = "" if result.get("ok") else obs
        messages.append({"role": "observation", "content": redact_secrets(obs)})

        if result.get("stop"):
            return {
                "ok": False,
                "stopped": True,
                "reason": obs,
                "turns": turns_used,
                "final": "",
                "observations": observations,
            }

    return {
        "ok": False,
        "stopped": False,
        "reason": f"Hit max_turns={max_turns} without a final answer.",
        "turns": turns_used,
        "final": "",
        "observations": observations,
    }
