"""Shared run state for live progress, Stop, stuck pause/resume, and Spice checklist."""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional


class VassalOpsRunController:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._continue = threading.Event()
        self._skip = threading.Event()
        self._state: Dict[str, Any] = self._idle_state()

    def _idle_state(self) -> Dict[str, Any]:
        return {
            "status": "idle",
            "phase": "",
            "current": 0,
            "total": 0,
            "label": "",
            "readable_steps": [],
            "checklist": [],
            "summary": "",
            "needs_you": "",
            "current_tool": "",
            "pending_replan": None,
            "last_error": "",
            "stuck_reason": "",
            "stuck_hint": "",
            "started_at": None,
            "finished_at": None,
            "ok": None,
        }

    def reset_for_run(self, readable_steps: Optional[list] = None, phase: str = "run") -> None:
        with self._lock:
            self._stop.clear()
            self._continue.clear()
            self._skip.clear()
            steps = list(readable_steps or [])
            self._state = self._idle_state()
            self._state["status"] = "running"
            self._state["phase"] = phase
            self._state["readable_steps"] = steps
            self._state["total"] = len(steps)
            self._state["checklist"] = [
                {"index": i, "label": str(label), "status": "pending"}
                for i, label in enumerate(steps)
            ]
            self._state["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._state)

    def set_progress(self, current: int, label: str) -> None:
        with self._lock:
            if self._state["status"] in ("stopped", "done"):
                return
            self._state["status"] = "running"
            self._state["current"] = current
            self._state["label"] = label
            self._state["current_tool"] = label
            self._state["stuck_reason"] = ""
            self._state["stuck_hint"] = ""
            checklist = self._state.get("checklist") or []
            # 1-based current: mark prior done, current running
            for item in checklist:
                idx = int(item.get("index", -1))
                if idx < current - 1 and item.get("status") == "pending":
                    item["status"] = "done"
                if idx == current - 1:
                    item["status"] = "running"
                    if label:
                        item["label"] = label

    def mark_checklist_status(self, index: int, status: str) -> None:
        with self._lock:
            for item in self._state.get("checklist") or []:
                if int(item.get("index", -1)) == index:
                    item["status"] = status
                    break

    def set_summary(self, text: str) -> None:
        with self._lock:
            self._state["summary"] = (text or "")[:800]
            # Parse ICM / Spice "Needs you:" line for the progress panel badge
            needs = ""
            for line in (text or "").splitlines():
                if line.lower().startswith("needs you:"):
                    needs = line.split(":", 1)[-1].strip()
                    break
            self._state["needs_you"] = needs[:300]

    def set_needs_you(self, text: str) -> None:
        with self._lock:
            self._state["needs_you"] = (text or "")[:300]

    def set_pending_replan(self, message: str, steps: Optional[List[str]] = None) -> None:
        """Spice: second Approve required before continuing a suggested replan."""
        with self._lock:
            self._state["pending_replan"] = {
                "message": (message or "")[:600],
                "steps": list(steps or [])[:20],
            }
            self._state["status"] = "paused"
            self._state["stuck_reason"] = "Replan suggested — Approve to continue."
            self._state["stuck_hint"] = message or "Review the suggested next steps, then Approve replan."

    def clear_pending_replan(self) -> None:
        with self._lock:
            self._state["pending_replan"] = None

    def confirm_replan(self) -> None:
        """Human second Approve for mid-run replan → resume like Continue."""
        with self._lock:
            self._state["pending_replan"] = None
            if self._state["status"] == "paused":
                self._state["status"] = "running"
                self._state["stuck_reason"] = ""
                self._state["stuck_hint"] = ""
        self._continue.set()

    def enter_stuck(self, reason: str, hint: str = "") -> None:
        with self._lock:
            self._state["status"] = "paused"
            self._state["stuck_reason"] = reason
            self._state["stuck_hint"] = hint or "Complete the blocking step (login / MFA / CAPTCHA), then Continue."
            if not self._state.get("summary"):
                self._state["summary"] = f"Stuck: {reason}"
            checklist = self._state.get("checklist") or []
            cur = int(self._state.get("current") or 0) - 1
            for item in checklist:
                if int(item.get("index", -1)) == cur and item.get("status") == "running":
                    item["status"] = "failed"
        self._continue.clear()
        self._skip.clear()

    def wait_while_paused(self, poll_seconds: float = 0.25) -> str:
        """
        Blocks while paused. Returns:
          continue | skip | stop
        """
        while True:
            if self._stop.is_set():
                return "stop"
            if self._skip.is_set():
                self._skip.clear()
                with self._lock:
                    if self._state["status"] == "paused":
                        self._state["status"] = "running"
                        self._state["stuck_reason"] = ""
                        self._state["pending_replan"] = None
                return "skip"
            if self._continue.is_set():
                self._continue.clear()
                with self._lock:
                    if self._state["status"] == "paused":
                        self._state["status"] = "running"
                        self._state["stuck_reason"] = ""
                return "continue"
            time.sleep(poll_seconds)

    def continue_run(self) -> None:
        self._continue.set()

    def skip_stuck_step(self) -> None:
        self._skip.set()

    def request_stop(self) -> None:
        self._stop.set()
        self._continue.set()
        self._skip.set()
        with self._lock:
            if self._state["status"] not in ("done", "idle"):
                self._state["status"] = "stopped"
                self._state["last_error"] = self._state.get("last_error") or "Stopped by user."
                self._state["summary"] = self._state.get("summary") or "Stopped by user."

    def stop_requested(self) -> bool:
        return self._stop.is_set()

    def finish(self, ok: bool, error: str = "") -> None:
        with self._lock:
            if self._state["status"] == "stopped":
                self._state["ok"] = False
            else:
                self._state["status"] = "done"
                self._state["ok"] = ok
            if error:
                self._state["last_error"] = error
            self._state["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            self._state["stuck_reason"] = ""
            # Keep pending_replan so the UI can still offer second Approve after the run ends.
            if ok:
                for item in self._state.get("checklist") or []:
                    if item.get("status") in ("pending", "running"):
                        item["status"] = "done"
                if not self._state.get("summary"):
                    self._state["summary"] = "Run completed successfully."
            else:
                if not self._state.get("summary"):
                    self._state["summary"] = error or "Run failed."

    def finish_if_active(self, ok: bool, error: str = "") -> bool:
        """Call finish only when the run is still in flight. Returns True if finish ran."""
        with self._lock:
            if self._state["status"] in ("done", "stopped"):
                return False
        self.finish(ok, error)
        return True


# Process-wide controller used by macros, duties, and the dashboard.
run_controller = VassalOpsRunController()
