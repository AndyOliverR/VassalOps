"""Last approved session snapshot for resume (still requires Approve for desktop tools)."""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List

from src.ingestion.secret_redactor import redact_secrets


SESSION_PATH = os.path.join("storage", "sessions", "last.json")


def save_last_session(
    *,
    goal: str,
    observations: List[str] = None,
    final: str = "",
    ok: bool = False,
    path: str = SESSION_PATH,
) -> str:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    payload: Dict[str, Any] = {
        "saved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "goal": redact_secrets(goal or ""),
        "observations": [redact_secrets(str(o)) for o in (observations or [])][-12:],
        "final": redact_secrets(final or ""),
        "ok": bool(ok),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return path.replace("\\", "/")


def load_last_session(path: str = SESSION_PATH) -> Dict[str, Any]:
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def format_resume_context(session: Dict[str, Any]) -> str:
    if not session:
        return ""
    obs = session.get("observations") or []
    tail = "\n".join(f"- {o}" for o in obs[-8:])
    return (
        f"[Resume context from {session.get('saved_at', 'unknown')}]\n"
        f"Prior goal: {session.get('goal')}\n"
        f"Prior ok: {session.get('ok')}\n"
        f"Prior final: {session.get('final')}\n"
        f"Recent observations:\n{tail or '(none)'}\n"
        "Continue this work. Desktop tools still require Approve."
    )
