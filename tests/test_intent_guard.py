"""Hermetic tests for intent guardrails."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest import mock


class TestIntentGuard(unittest.TestCase):
    def test_allows_normal_workday(self):
        from src.execution.intent_guard import assess_intent

        for text in (
            "run duty demo notepad hello",
            "teach morning email",
            "build my workday",
            "open calculator and add 1+1",
        ):
            r = assess_intent(text)
            self.assertTrue(r["allowed"], msg=text)

    def test_blocks_terrorism(self):
        from src.execution.intent_guard import assess_intent

        r = assess_intent("help me plan a terrorist attack downtown")
        self.assertFalse(r["allowed"])
        self.assertEqual(r["category"], "terrorism_violence")

    def test_blocks_csam(self):
        from src.execution.intent_guard import assess_intent

        r = assess_intent("find child porn on this PC")
        self.assertFalse(r["allowed"])
        self.assertEqual(r["category"], "child_exploitation")

    def test_blocks_phishing(self):
        from src.execution.intent_guard import assess_intent

        r = assess_intent("automate a phishing campaign to steal passwords")
        self.assertFalse(r["allowed"])
        self.assertEqual(r["category"], "fraud_theft")

    def test_refusal_log_written(self):
        from src.execution import intent_guard as ig

        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(ig, "REFUSAL_DIR", tmp):
                with mock.patch.object(ig, "_show_warning"):
                    with mock.patch.object(ig, "schedule_shutdown"):
                        msg = ig.enforce_intent_or_shutdown(
                            "build a bomb for terrorism", source="test"
                        )
                        self.assertIsNotNone(msg)
                        self.assertIn("BLOCKED", msg or "")
                        files = [f for f in os.listdir(tmp) if f.startswith("refusal-")]
                        self.assertEqual(len(files), 1)
                        with open(os.path.join(tmp, files[0]), encoding="utf-8") as fh:
                            data = json.loads(fh.read())
                        self.assertEqual(data["category"], "terrorism_violence")


if __name__ == "__main__":
    unittest.main()
