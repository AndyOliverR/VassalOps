"""Named daily-duty library built on macro record/replay files."""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, List, Optional


DUTIES_DIR = os.path.join("storage", "duties")
PLAYLIST_PATH = os.path.join(DUTIES_DIR, "playlist.json")


def _slugify(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_\-\s]", "", name.strip().lower())
    cleaned = re.sub(r"\s+", "_", cleaned).strip("_")
    return cleaned or "duty"


class VassalOpsDutyLibrary:
    def __init__(self, duties_dir: str = DUTIES_DIR):
        self.duties_dir = duties_dir
        os.makedirs(self.duties_dir, exist_ok=True)

    def duty_path(self, duty_id: str) -> str:
        safe = _slugify(duty_id.replace(".json", ""))
        return os.path.join(self.duties_dir, f"{safe}.json")

    def list_duties(self) -> List[Dict[str, Any]]:
        duties = []
        if not os.path.isdir(self.duties_dir):
            return duties
        for name in sorted(os.listdir(self.duties_dir)):
            if not name.endswith(".json") or name == "playlist.json":
                continue
            path = os.path.join(self.duties_dir, name)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                duties.append({
                    "id": data.get("id", name[:-5]),
                    "name": data.get("name", name[:-5]),
                    "description": data.get("description", ""),
                    "tags": data.get("tags", []),
                    "created_at": data.get("created_at"),
                    "last_run": data.get("last_run"),
                    "success_count": data.get("success_count", 0),
                    "step_count": len(data.get("steps") or []),
                })
            except Exception:
                continue
        return duties

    def get_duty(self, duty_id: str) -> Optional[Dict[str, Any]]:
        path = self.duty_path(duty_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def resolve_macro_relpath(self, duty_id: str) -> str:
        """Path relative to storage/ for MacroPlayer/Recorder (storage/<rel>)."""
        safe = _slugify(duty_id.replace(".json", ""))
        return os.path.join("duties", f"{safe}.json").replace("\\", "/")

    def start_teach(self, display_name: str, description: str = "") -> Dict[str, Any]:
        """
        Records a duty interactively (blocks until Escape), then writes metadata + steps.
        Warns that keystrokes may include passwords.
        """
        from src.execution.macro_recorder import VassalOpsMacroRecorder

        duty_id = _slugify(display_name)
        rel = self.resolve_macro_relpath(duty_id)
        print("[VassalOps Duties] TEACH MODE WARNING: Keystrokes are recorded and may include passwords.")
        print("[VassalOps Duties] Prefer click-only flows for logins when possible. Press Escape to finish.")

        recorder = VassalOpsMacroRecorder(output_filename=rel.replace("/", os.sep))
        recorder.start_recording()

        # Enrich the raw steps file with duty metadata
        path = self.duty_path(duty_id)
        steps = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                steps = raw.get("steps", raw if isinstance(raw, list) else [])
            except Exception:
                steps = []

        payload = {
            "id": duty_id,
            "name": display_name.strip() or duty_id,
            "description": description or f"Taught duty: {display_name}",
            "tags": ["taught"],
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "last_run": None,
            "success_count": 0,
            "steps": steps,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return payload

    def run_duty(self, duty_id: str) -> Dict[str, Any]:
        """Replay a duty; stop-on-failure is handled by caller for playlists."""
        from src.execution.macro_player import VassalOpsMacroPlayer

        duty = self.get_duty(duty_id)
        if not duty:
            return {"ok": False, "duty_id": duty_id, "error": "Duty not found."}
        if not duty.get("steps"):
            return {"ok": False, "duty_id": duty_id, "error": "Duty has no recorded steps."}

        # Ensure player-readable shape (steps at top level already)
        rel = self.resolve_macro_relpath(duty_id)
        # Player expects {"steps": [...]} which duty files have
        player = VassalOpsMacroPlayer(target_filename=rel.replace("/", os.sep))
        ok = player.execute_replay()
        self._mark_run(duty_id, success=bool(ok))
        return {"ok": bool(ok), "duty_id": duty_id, "name": duty.get("name", duty_id)}

    def _mark_run(self, duty_id: str, success: bool) -> None:
        duty = self.get_duty(duty_id)
        if not duty:
            return
        duty["last_run"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        if success:
            duty["success_count"] = int(duty.get("success_count") or 0) + 1
        path = self.duty_path(duty_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(duty, f, indent=2)

    def format_duty_list(self) -> str:
        duties = self.list_duties()
        if not duties:
            return "No duties taught yet. Say: teach morning email check"
        lines = ["Your taught duties:"]
        for d in duties:
            lines.append(
                f"- {d['name']} (id: {d['id']}, steps: {d['step_count']}, "
                f"runs: {d['success_count']}, last: {d['last_run'] or 'never'})"
            )
        return "\n".join(lines)

    def import_demo_packs(self) -> Dict[str, Any]:
        """Copy safe sample duties from storage/duties/packs into the duty library."""
        packs_dir = os.path.join(self.duties_dir, "packs")
        imported = []
        if not os.path.isdir(packs_dir):
            return {"ok": False, "imported": [], "error": "No packs folder found."}
        for name in sorted(os.listdir(packs_dir)):
            if not name.endswith(".json"):
                continue
            src = os.path.join(packs_dir, name)
            try:
                with open(src, "r", encoding="utf-8") as f:
                    data = json.load(f)
                duty_id = data.get("id") or name[:-5]
                dest = self.duty_path(duty_id)
                data["id"] = duty_id
                with open(dest, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                imported.append(duty_id)
            except Exception as exc:
                return {"ok": False, "imported": imported, "error": str(exc)}

        # ICM staged packs (folder + CONTEXT.md + duty.json per stage)
        from src.execution.staged_pack import import_staged_packs

        staged = import_staged_packs(self)
        if not staged.get("ok"):
            return {
                "ok": False,
                "imported": imported,
                "imported_packs": staged.get("imported_packs") or [],
                "error": staged.get("error") or "Staged pack import failed",
            }
        imported.extend(staged.get("imported_duties") or [])
        return {
            "ok": True,
            "imported": imported,
            "imported_packs": staged.get("imported_packs") or [],
        }


def extract_duty_name_from_command(user_input: str, keyword: str) -> str:
    """Pull a human duty name from phrases like 'teach morning email check'."""
    name, _note = extract_teach_parts(user_input, keyword)
    return name


def extract_teach_parts(user_input: str, keyword: str = "teach") -> tuple:
    """
    Parse 'teach morning email: triage inbox' into (name, note).
    Also used for 'run duty …' (note ignored).
    """
    lowered = user_input.lower()
    idx = lowered.find(keyword)
    if idx < 0:
        return "unnamed_duty", ""
    remainder = user_input[idx + len(keyword):].strip(" ,.-")
    tokens = remainder.split()
    noise = {"please", "now", "duty", "for", "me"}
    while tokens and tokens[0].lower().strip(",.") in noise:
        if tokens[0].lower() == "for" and len(tokens) > 1 and tokens[1].lower() == "me":
            tokens = tokens[2:]
            continue
        tokens = tokens[1:]
    while tokens and tokens[-1].lower().strip(",.").rstrip("?") in noise:
        tokens = tokens[:-1]
    name = " ".join(tokens).strip()
    note = ""
    for sep in (":", "—", " – ", " - "):
        if sep in name:
            left, _, right = name.partition(sep)
            name, note = left.strip(), right.strip()
            break
    return (name or "unnamed_duty"), note
