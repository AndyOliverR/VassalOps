"""Sanitized workday skill shapes for lab-rat handshake (no documents, no keystrokes)."""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional

from src.ingestion.secret_redactor import redact_secrets


APP_FAMILIES = (
    ("outlook", ("outlook", "microsoft outlook")),
    ("excel", ("excel", "microsoft excel")),
    ("word", ("microsoft word", "word")),
    ("chrome", ("google chrome", "chrome")),
    ("edge", ("microsoft edge", "edge")),
    ("firefox", ("firefox", "mozilla firefox")),
    ("notepad", ("notepad",)),
    ("explorer", ("file explorer", "explorer")),
    ("teams", ("microsoft teams", "teams")),
    ("calculator", ("calculator",)),
)

_PATH_RE = re.compile(r"[A-Za-z]:\\[^\s]+|\\\\[^\s]+|/[^\s]+")
_STEP_TYPE_RE = re.compile(r"^[a-z][a-z0-9_]{0,40}$")


def _workspace_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _generic_app_family(title: str) -> str:
    low = (title or "").strip().lower()
    if not low:
        return ""
    for family, needles in APP_FAMILIES:
        if any(n in low for n in needles):
            return family
    return "other"


def _safe_step_type(raw: Any) -> str:
    text = str(raw or "unknown").strip().lower().replace(" ", "_")
    if not _STEP_TYPE_RE.match(text):
        return "unknown"
    return text[:40]


def sanitize_steps(steps: Iterable[Any]) -> List[str]:
    """Return step *types* only — never coordinates, keystrokes, or typed text."""
    out: List[str] = []
    for step in steps or []:
        if isinstance(step, dict):
            kind = step.get("type") or step.get("action") or "unknown"
        else:
            kind = "unknown"
        out.append(_safe_step_type(kind))
        if len(out) >= 40:
            break
    return out


def _generic_duty_id(duty_id: str) -> str:
    slug = re.sub(r"[^a-z0-9_]+", "_", (duty_id or "duty").strip().lower()).strip("_")
    slug = redact_secrets(slug)
    return (slug or "duty")[:80]


def _scrub_line(text: str, limit: int = 160) -> str:
    line = redact_secrets((text or "").strip())
    line = _PATH_RE.sub("[REDACTED_PATH]", line)
    line = re.sub(r"\s+", " ", line)
    return line[:limit]


def _duty_shapes(duties_dir: str) -> List[Dict[str, Any]]:
    shapes: List[Dict[str, Any]] = []
    if not os.path.isdir(duties_dir):
        return shapes
    for name in sorted(os.listdir(duties_dir)):
        if not name.endswith(".json") or name == "playlist.json":
            continue
        path = os.path.join(duties_dir, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        steps = sanitize_steps(data.get("steps") or [])
        families: List[str] = []
        for step in data.get("steps") or []:
            if isinstance(step, dict):
                fam = _generic_app_family(str(step.get("window_title") or ""))
                if fam and fam not in families:
                    families.append(fam)
        shapes.append(
            {
                "id": _generic_duty_id(str(data.get("id") or name[:-5])),
                "step_types": steps,
                "step_count": len(steps),
                "success_count": int(data.get("success_count") or 0),
                "app_families": families[:6],
                "taught": "taught" in [str(t).lower() for t in (data.get("tags") or [])],
            }
        )
        if len(shapes) >= 40:
            break
    return shapes


def _looks_like_inventory(text: str) -> bool:
    low = (text or "").lower()
    return (
        "internal catalog" in low
        or "internal_data" in low
        or "sample_availability" in low
    )


def _agent_lessons(memory_path: str) -> List[str]:
    if not os.path.isfile(memory_path):
        return []
    try:
        with open(memory_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return []
    bullets: List[str] = []
    in_section = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            in_section = line.lower() in ("## lessons", "## preferences")
            continue
        if in_section and line.startswith("- "):
            if _looks_like_inventory(line):
                continue
            cleaned = _scrub_line(line[2:])
            if len(cleaned) >= 8:
                bullets.append(cleaned)
            if len(bullets) >= 12:
                break
    return bullets


def _reflex_families(reflex_dir: str) -> List[str]:
    if not os.path.isdir(reflex_dir):
        return []
    families: List[str] = []
    for name in sorted(os.listdir(reflex_dir)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(reflex_dir, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        titles = []
        if isinstance(data, dict):
            titles = list(data.get("window_titles") or [])
        for title in titles:
            fam = _generic_app_family(str(title))
            if fam and fam not in families:
                families.append(fam)
        if len(families) >= 8:
            break
    return families


def build_skill_distillate(
    root: Optional[str] = None,
    *,
    install_id: str = "",
    version: str = "",
    reason: str = "launch",
) -> Dict[str, Any]:
    """Public, privacy-safe packet: how work is shaped, not what the business did."""
    base = root if root is not None else _workspace_root()
    duties_dir = os.path.join(base, "storage", "duties")
    memory_path = os.path.join(base, "storage", "agent.md")
    reflex_dir = os.path.join(base, "storage", "reflexes")
    duties = _duty_shapes(duties_dir)
    type_counts: Counter[str] = Counter()
    for duty in duties:
        type_counts.update(duty.get("step_types") or [])
    return {
        "app": "VassalOps",
        "kind": "skill_distillate",
        "schema": 1,
        "reason": reason,
        "version": version,
        "install_id": install_id,
        "duty_count": len(duties),
        "duties": duties,
        "step_type_counts": dict(type_counts),
        "lessons": _agent_lessons(memory_path),
        "app_families": _reflex_families(reflex_dir),
        "privacy": "no_documents_no_keystrokes_no_screens_no_inventory",
    }
