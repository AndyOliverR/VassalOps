import os
import tempfile
import unittest
from src.execution.duty_library import (
    VassalOpsDutyLibrary,
    extract_duty_name_from_command,
    extract_teach_parts,
    _slugify,
)
from src.execution.daily_playlist import VassalOpsDailyPlaylist
from src.execution.session_store import save_last_duty, load_last_duty


class TestDutyLibrary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="vassal_duties_")
        self.lib = VassalOpsDutyLibrary(duties_dir=self.tmp)

    def test_slugify_and_extract(self):
        self.assertEqual(_slugify("Morning Email!"), "morning_email")
        self.assertEqual(extract_duty_name_from_command("teach morning email please", "teach"), "morning email")

    def test_extract_teach_with_note(self):
        name, note = extract_teach_parts("teach morning email: triage inbox", "teach")
        self.assertEqual(name, "morning email")
        self.assertEqual(note, "triage inbox")

    def test_last_duty_roundtrip(self):
        path = os.path.join(self.tmp, "last_duty.json")
        save_last_duty(duty_id="morning_email", name="morning email", note="triage", path=path)
        data = load_last_duty(path)
        self.assertEqual(data["duty_id"], "morning_email")
        self.assertEqual(data["note"], "triage")

    def test_list_empty(self):
        self.assertEqual(self.lib.list_duties(), [])
        self.assertIn("No duties", self.lib.format_duty_list())

    def test_playlist_build_and_today(self):
        path = os.path.join(self.tmp, "demo.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write('{"id":"demo","name":"Demo","steps":[{"type":"click","x":1,"y":2}],"success_count":0}')
        playlist_path = os.path.join(self.tmp, "playlist.json")
        pl = VassalOpsDailyPlaylist(playlist_path=playlist_path, library=self.lib)
        pl.build_workday_from_all_duties(start_hour=9, gap_minutes=15)
        briefing = pl.get_today_playlist()
        self.assertEqual(len(briefing["items"]), 1)
        self.assertEqual(briefing["items"][0]["duty_id"], "demo")
        self.assertTrue(briefing["items"][0]["exists"])

    def test_stop_on_failure(self):
        for name in ("a", "b"):
            with open(os.path.join(self.tmp, f"{name}.json"), "w", encoding="utf-8") as f:
                f.write(f'{{"id":"{name}","name":"{name}","steps":[],"success_count":0}}')
        playlist_path = os.path.join(self.tmp, "playlist.json")
        pl = VassalOpsDailyPlaylist(playlist_path=playlist_path, library=self.lib)
        pl.build_workday_from_all_duties()
        report = pl.run_playlist(["a", "b"])
        self.assertFalse(report["ok"])
        self.assertEqual(len(report["results"]), 1)
        self.assertTrue(report["stopped_early"])


if __name__ == "__main__":
    unittest.main()
