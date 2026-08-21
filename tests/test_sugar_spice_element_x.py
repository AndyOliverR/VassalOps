"""Hermetic tests for Sugar / Spice / Element X / workspace tools."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


class TestDutyReflex(unittest.TestCase):
    def test_save_and_find_reflex(self):
        from src.execution import duty_reflex as dr

        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(dr, "REFLEX_DIR", tmp):
                path = dr.save_reflex(
                    duty_id="demo-notepad-hello",
                    goal="run duty demo notepad hello",
                    observations=[
                        "focus_window: Focused window matching 'Notepad'. Active window: Untitled - Notepad.",
                        "Could not find on-screen text “Hello”.",
                    ],
                )
                self.assertTrue(os.path.isfile(path))
                data = dr.load_reflex("demo-notepad-hello")
                self.assertIsNotNone(data)
                self.assertIn("Notepad", " ".join(data.get("window_titles") or []))
                hits = dr.find_reflexes("notepad")
                self.assertTrue(hits)
                ctx = dr.format_reflex_context(duty_id="demo-notepad-hello")
                self.assertIn("DUTY REFLEX", ctx)


class TestWorkspaceFiles(unittest.TestCase):
    def test_path_escape_rejected(self):
        from src.execution.workspace_files import resolve_workspace_path, write_workspace_file

        ok, _, err = resolve_workspace_path("../etc/passwd")
        self.assertFalse(ok)
        self.assertIn("..", err)
        msg = write_workspace_file("README.md", "x", approved=False)
        self.assertIn("blocked", msg)

    def test_list_and_read_readme(self):
        from src.execution.workspace_files import list_workspace_dir, read_workspace_file

        listing = list_workspace_dir(".")
        self.assertIn("list_dir", listing)
        text = read_workspace_file("VERSION")
        self.assertTrue(text.strip())


class TestRunControllerChecklist(unittest.TestCase):
    def test_checklist_and_replan(self):
        from src.execution.run_controller import VassalOpsRunController

        c = VassalOpsRunController()
        c.reset_for_run(["Step A", "Step B"], phase="test")
        snap = c.snapshot()
        self.assertEqual(len(snap["checklist"]), 2)
        self.assertEqual(snap["checklist"][0]["status"], "pending")
        c.set_progress(1, "Step A running")
        self.assertEqual(c.snapshot()["checklist"][0]["status"], "running")
        c.set_pending_replan("Try again", ["Continue goal"])
        self.assertIsNotNone(c.snapshot()["pending_replan"])
        c.confirm_replan()
        self.assertIsNone(c.snapshot()["pending_replan"])
        self.assertEqual(c.snapshot()["status"], "running")


class TestLandmarkRetryHelper(unittest.TestCase):
    def test_resolve_with_retries_exists(self):
        from src.execution.landmark_target import resolve_click_point_with_retries

        # Missing x/y and no landmark -> fails after retries (no GUI required)
        result = resolve_click_point_with_retries(
            {"type": "click"},
            max_auto_retries=1,
            delay=0.01,
        )
        self.assertFalse(result.get("ok"))
        self.assertTrue(result.get("auto_exhausted"))


class TestFirewallNewTools(unittest.TestCase):
    def test_workspace_tools_allowlisted(self):
        from src.execution.action_firewall import VassalOpsActionFirewall

        fw = VassalOpsActionFirewall()
        self.assertEqual(fw.verify_step({"type": "list_dir", "payload": "."})["status"], "VERIFIED")
        self.assertEqual(fw.verify_step({"type": "read_file", "payload": "VERSION"})["status"], "VERIFIED")
        self.assertEqual(fw.verify_step({"type": "run_unittest", "payload": ""})["status"], "VERIFIED")
        self.assertEqual(fw.verify_step({"type": "write_file", "payload": ""})["status"], "REJECTED")


if __name__ == "__main__":
    unittest.main()
