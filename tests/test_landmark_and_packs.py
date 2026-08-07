import os
import tempfile
import unittest
from src.execution.duty_library import VassalOpsDutyLibrary
from src.execution.action_firewall import VassalOpsActionFirewall
from src.execution.landmark_target import resolve_click_point


class TestLandmarkResolve(unittest.TestCase):
    def test_coords_only(self):
        result = resolve_click_point({"type": "click", "x": 12, "y": 34})
        self.assertTrue(result["ok"])
        self.assertEqual(result["x"], 12)
        self.assertEqual(result["y"], 34)


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


class TestFirewallLandmarks(unittest.TestCase):
    def test_focus_and_landmark(self):
        fw = VassalOpsActionFirewall()
        self.assertEqual(fw.verify_step({"type": "focus_window", "payload": "Notepad"})["status"], "VERIFIED")
        self.assertEqual(fw.verify_step({"type": "click_landmark", "payload": "Send"})["status"], "VERIFIED")


if __name__ == "__main__":
    unittest.main()
