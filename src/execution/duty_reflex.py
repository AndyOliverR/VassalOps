"""Element X — Duty Reflex: procedural memory from successful Approve runs."""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, List, Optional


REFLEX_DIR = os.path.join("storage", "reflexes")


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").strip().lower()).strip("-")
    return (s[:80] or "goal") 


def ensure_reflex_dir() -> str:
    os.makedirs(REFLEX_DIR, exist_ok=True)
    return REFLEX_DIR


def reflex_path(key: str) -> str:
    ensure_reflex_dir()
    return os.path.join(REFLEX_DIR, f"{_slug(key)}.json")


def extract_reflex_signals(observations: List[str], *, duty_id: str = "", goal: str = "") -> Dict[str, Any]:
    """Pull window titles / landmarks mentioned in observation strings."""
    titles: List[str] = []
    landmarks: List[str] = []
    for obs in observations or []:
        text = str(obs)
        for m in re.finditer(r"Focused window matching '([^']+)'", text):
            titles.append(m.group(1))
        for m in re.finditer(r"window[^\n]{0,40}?“([^”]+)”", text, re.I):
            titles.append(m.group(1))
        for m in re.finditer(r"landmark[^\n]{0,20}?“([^”]+)”", text, re.I):
            landmarks.append(m.group(1))
        for m in re.finditer(r"Active window:\s*([^\n.]+)", text):
            titles.append(m.group(1).strip())
    # dedupe preserve order
    def uniq(items: List[str]) -> List[str]:
        seen = set()
        out = []
        for i in items:
            k = i.strip().lower()
            if not k or k in seen:
                continue
            seen.add(k)
            out.append(i.strip())
        return out[:12]

    return {
        "duty_id": duty_id or "",
        "goal": (goal or "")[:240],
        "window_titles": uniq(titles),
        "landmarks": uniq(landmarks),
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "ok": True,
    }


def save_reflex(
    *,
    duty_id: str = "",
    goal: str = "",
    observations: Optional[List[str]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """Persist reflex JSON for a duty or goal key. Returns path written."""
    key = duty_id or goal or "anonymous"
    payload = extract_reflex_signals(observations or [], duty_id=duty_id, goal=goal)
    if extra:
        payload.update(extra)
    path = reflex_path(key)
    # Merge with previous if present
    prev: Dict[str, Any] = {}
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                prev = json.load(f)
        except Exception:
            prev = {}
    for field in ("window_titles", "landmarks"):
        merged = list(prev.get(field) or []) + list(payload.get(field) or [])
        seen = set()
        clean = []
        for item in merged:
            k = str(item).strip().lower()
            if not k or k in seen:
                continue
            seen.add(k)
            clean.append(str(item).strip())
        payload[field] = clean[:12]
    if prev.get("goal") and not payload.get("goal"):
        payload["goal"] = prev["goal"]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return path


def load_reflex(key: str) -> Optional[Dict[str, Any]]:
    path = reflex_path(key)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def find_reflexes(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Keyword match over reflex files (duty id, goal, titles, landmarks)."""
    ensure_reflex_dir()
    tokens = [t for t in re.split(r"\W+", (query or "").lower()) if t]
    if not tokens:
        return []
    hits: List[Dict[str, Any]] = []
    for name in os.listdir(REFLEX_DIR):
        if not name.endswith(".json"):
            continue
        path = os.path.join(REFLEX_DIR, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        blob = " ".join(
            [
                str(data.get("duty_id") or ""),
                str(data.get("goal") or ""),
                " ".join(data.get("window_titles") or []),
                " ".join(data.get("landmarks") or []),
                name,
            ]
        ).lower()
        if any(tok in blob for tok in tokens):
            hits.append(data)
        if len(hits) >= limit:
            break
    return hits[:limit]


def format_reflex_context(goal: str = "", duty_id: str = "") -> str:
    """Text block injected into agent loop / planner (never skips Approve)."""
    keys = []
    if duty_id:
        keys.append(duty_id)
    if goal:
        keys.append(goal)
    reflexes: List[Dict[str, Any]] = []
    for key in keys:
        data = load_reflex(key)
        if data:
            reflexes.append(data)
    if goal and not reflexes:
        reflexes = find_reflexes(goal, limit=3)
    if not reflexes:
        return ""
    lines = ["DUTY REFLEX (Element X — prior Approve successes; still require human Approve):"]
    for r in reflexes[:3]:
        lines.append(
            f"- duty={r.get('duty_id') or '(goal)'} titles={r.get('window_titles') or []} "
            f"landmarks={r.get('landmarks') or []}"
        )
    return "\n".join(lines)
