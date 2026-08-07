"""Daily workday playlist: schedule taught duties and run them sequentially."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.execution.duty_library import DUTIES_DIR, PLAYLIST_PATH, VassalOpsDutyLibrary


DEFAULT_PLAYLIST = {
    "workday": [],
    "policy": {
        "stop_on_failure": True,
        "require_approval": True,
    },
}


class VassalOpsDailyPlaylist:
    def __init__(
        self,
        playlist_path: str = PLAYLIST_PATH,
        library: Optional[VassalOpsDutyLibrary] = None,
        ledger=None,
    ):
        self.playlist_path = playlist_path
        self.library = library or VassalOpsDutyLibrary()
        self.ledger = ledger
        os.makedirs(os.path.dirname(self.playlist_path) or DUTIES_DIR, exist_ok=True)
        if not os.path.exists(self.playlist_path):
            self.save(DEFAULT_PLAYLIST)

    def load(self) -> Dict[str, Any]:
        try:
            with open(self.playlist_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "workday" not in data:
                data["workday"] = []
            if "policy" not in data:
                data["policy"] = dict(DEFAULT_PLAYLIST["policy"])
            return data
        except Exception:
            return dict(DEFAULT_PLAYLIST)

    def save(self, data: Dict[str, Any]) -> None:
        with open(self.playlist_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def add_duty(self, duty_id: str, after: str = "09:00", required: bool = True) -> Dict[str, Any]:
        data = self.load()
        # replace existing entry for same duty_id
        data["workday"] = [e for e in data["workday"] if e.get("duty_id") != duty_id]
        data["workday"].append({"duty_id": duty_id, "after": after, "required": required})
        data["workday"].sort(key=lambda e: e.get("after") or "00:00")
        self.save(data)
        return data

    def remove_duty(self, duty_id: str) -> Dict[str, Any]:
        data = self.load()
        data["workday"] = [e for e in data["workday"] if e.get("duty_id") != duty_id]
        self.save(data)
        return data

    def get_today_playlist(self) -> Dict[str, Any]:
        """Returns today's briefing items with duty metadata. Filters by local time 'after'."""
        data = self.load()
        now = datetime.now()
        now_hm = now.strftime("%H:%M")
        items = []
        for entry in data.get("workday", []):
            duty_id = entry.get("duty_id")
            duty = self.library.get_duty(duty_id) if duty_id else None
            after = entry.get("after") or "00:00"
            items.append({
                "duty_id": duty_id,
                "after": after,
                "required": bool(entry.get("required", True)),
                "due": after <= now_hm,
                "name": (duty or {}).get("name", duty_id),
                "step_count": len((duty or {}).get("steps") or []),
                "exists": duty is not None,
                "last_run": (duty or {}).get("last_run"),
            })
        return {
            "date": now.strftime("%Y-%m-%d"),
            "time": now_hm,
            "items": items,
            "policy": data.get("policy", DEFAULT_PLAYLIST["policy"]),
        }

    def run_playlist(self, duty_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Sequentially replay duties. Stops on first failure when policy.stop_on_failure is true.
        """
        data = self.load()
        stop_on_failure = bool(data.get("policy", {}).get("stop_on_failure", True))
        briefing = self.get_today_playlist()
        selected = duty_ids
        if not selected:
            selected = [i["duty_id"] for i in briefing["items"] if i.get("exists")]

        results = []
        for duty_id in selected:
            if self.ledger:
                self.ledger.commit_transaction(
                    intent=f"playlist_run:{duty_id}",
                    status="STARTED",
                    device="daily_playlist",
                    channel="workday",
                )
            outcome = self.library.run_duty(duty_id)
            status = "success_completed" if outcome.get("ok") else "failed"
            if self.ledger:
                self.ledger.commit_transaction(
                    intent=f"playlist_run:{duty_id}",
                    status=status,
                    device="daily_playlist",
                    channel="workday",
                )
            results.append(outcome)
            if not outcome.get("ok") and stop_on_failure:
                break

        ok_all = all(r.get("ok") for r in results) if results else False
        return {
            "ok": ok_all,
            "stopped_early": (not ok_all) and stop_on_failure and len(results) < len(selected),
            "results": results,
        }

    def build_workday_from_all_duties(self, start_hour: int = 9, gap_minutes: int = 30) -> Dict[str, Any]:
        """Helper for 'build my workday': schedule every taught duty in list order."""
        duties = self.library.list_duties()
        data = self.load()
        workday = []
        minutes = start_hour * 60
        for d in duties:
            hh = minutes // 60
            mm = minutes % 60
            workday.append({
                "duty_id": d["id"],
                "after": f"{hh:02d}:{mm:02d}",
                "required": True,
            })
            minutes += gap_minutes
        data["workday"] = workday
        self.save(data)
        return data
