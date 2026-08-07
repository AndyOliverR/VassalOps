"""Shared run state for live progress, Stop, and stuck pause/resume."""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, Optional


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
            self._state = self._idle_state()
            self._state["status"] = "running"
            self._state["phase"] = phase
            self._state["readable_steps"] = list(readable_steps or [])
            self._state["total"] = len(self._state["readable_steps"])
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
            self._state["stuck_reason"] = ""
            self._state["stuck_hint"] = ""

    def request_stop(self) -> None:
        self._stop.set()
        self._continue.set()
        self._skip.set()
        with self._lock:
            if self._state["status"] not in ("done", "idle"):
                self._state["status"] = "stopped"
                self._state["last_error"] = self._state.get("last_error") or "Stopped by user."

    def stop_requested(self) -> bool:
        return self._stop.is_set()

    def enter_stuck(self, reason: str, hint: str = "") -> None:
        with self._lock:
            self._state["status"] = "paused"
            self._state["stuck_reason"] = reason
            self._state["stuck_hint"] = hint or "Complete the blocking step (login / MFA / CAPTCHA), then Continue."
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


# Process-wide controller used by macros, duties, and the dashboard.
run_controller = VassalOpsRunController()
