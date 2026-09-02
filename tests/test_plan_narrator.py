import json
import unittest
from src.execution.plan_narrator import narrate_proposed_actions, narrate_macro_steps
from src.execution.run_controller import VassalOpsRunController


class TestPlanNarrator(unittest.TestCase):
    def test_narrate_actions(self):
        lines = narrate_proposed_actions([
            {"type": "teach_duty", "payload": "morning email"},
            {"type": "speak_log", "payload": "Ready after Approve."},
            {"type": "read_internal_sheet", "payload": json.dumps({"url": "https://docs.google.com/spreadsheets/d/abc/edit", "query": "hotel"})},
        ])
        self.assertEqual(len(lines), 3)
        self.assertIn("morning email", lines[0])
        self.assertIn("Ready after Approve", lines[1])
        self.assertIn("spreadsheets", lines[2])

    def test_narrate_macro(self):
        lines = narrate_macro_steps([
            {"type": "focus_window", "title": "Notepad"},
            {"type": "click", "x": 10, "y": 20, "window_title": "Notepad"},
        ])
        self.assertIn("Notepad", lines[0])
        self.assertIn("Click", lines[1])


class TestRunController(unittest.TestCase):
    def test_stop_and_finish(self):
        c = VassalOpsRunController()
        c.reset_for_run(["1. A", "2. B"], phase="test")
        c.set_progress(1, "1. A")
        self.assertEqual(c.snapshot()["status"], "running")
        c.request_stop()
        self.assertTrue(c.stop_requested())
        self.assertEqual(c.snapshot()["status"], "stopped")


if __name__ == "__main__":
    unittest.main()
