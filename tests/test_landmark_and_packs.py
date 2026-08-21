import os
import tempfile
import unittest
from src.execution.duty_library import VassalOpsDutyLibrary
from src.execution.action_firewall import VassalOpsActionFirewall
from src.execution.landmark_target import resolve_click_point, score_title_match, normalize_title


class TestLandmarkResolve(unittest.TestCase):
    def test_coords_only(self):
        result = resolve_click_point({"type": "click", "x": 12, "y": 34})
        self.assertTrue(result["ok"])
        self.assertEqual(result["x"], 12)
        self.assertEqual(result["y"], 34)


class TestTitleMatchScoring(unittest.TestCase):
    def test_normalize_collapses_space(self):
        self.assertEqual(normalize_title("  Foo   Bar  "), "foo bar")

    def test_exact_beats_substring(self):
        exact = score_title_match("Calculator", "Calculator")
        longer = score_title_match("Calculator", "Calculator - Something else")
        self.assertGreater(exact, longer)
        self.assertGreater(exact, 0)

    def test_shorter_substring_preferred(self):
        short = score_title_match("Notepad", "Notepad")
        long = score_title_match("Notepad", "Untitled - Notepad - Extra")
        self.assertGreaterEqual(short, long)

    def test_no_match(self):
        self.assertEqual(score_title_match("Excel", "Notepad"), 0)

    def test_word_tokens(self):
        score = score_title_match("mail inbox", "Inbox - Mail")
        self.assertGreater(score, 0)


class TestDemoPackImport(unittest.TestCase):
    def test_import_pack(self):
        tmp = tempfile.mkdtemp(prefix="vassal_packs_")
        packs = os.path.join(tmp, "packs")
        os.makedirs(packs)
        with open(os.path.join(packs, "demo.json"), "w", encoding="utf-8") as f:
            f.write('{"id":"demo_x","name":"Demo X","steps":[{"type":"wait","seconds":0.1}]}')
        lib = VassalOpsDutyLibrary(duties_dir=tmp)
        result = lib.import_demo_packs()
        self.assertTrue(result["ok"])
        self.assertIn("demo_x", result["imported"])
        self.assertIsNotNone(lib.get_duty("demo_x"))

    def test_repo_packs_include_calculator(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        packs = os.path.join(root, "storage", "duties", "packs")
        calc = os.path.join(packs, "demo_calculator_one_plus_one.json")
        self.assertTrue(os.path.isfile(calc), "Calculator demo pack missing")


class TestFirewallLandmarks(unittest.TestCase):
    def test_focus_and_landmark(self):
        fw = VassalOpsActionFirewall()
        self.assertEqual(fw.verify_step({"type": "focus_window", "payload": "Notepad"})["status"], "VERIFIED")
        self.assertEqual(fw.verify_step({"type": "click_landmark", "payload": "Send"})["status"], "VERIFIED")


if __name__ == "__main__":
    unittest.main()
