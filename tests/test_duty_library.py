import os
import tempfile
import unittest
from src.execution.duty_library import VassalOpsDutyLibrary, extract_duty_name_from_command, _slugify
from src.execution.daily_playlist import VassalOpsDailyPlaylist


class TestDutyLibrary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="vassal_duties_")
        self.lib = VassalOpsDutyLibrary(duties_dir=self.tmp)

    def test_slugify_and_extract(self):
        self.assertEqual(_slugify("Morning Email!"), "morning_email")
        self.assertEqual(extract_duty_name_from_command("teach morning email please", "teach"), "morning email")

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
