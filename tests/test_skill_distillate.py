"""Hermetic tests for sanitized skill distillate (no documents / keystrokes)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.execution.skill_distillate import build_skill_distillate, sanitize_steps


class TestSkillDistillate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        duties = Path(self.root, "storage", "duties")
        duties.mkdir(parents=True)
        payload = {
            "id": "morning_email",
            "name": "Acme invoices for user@example.com",
            "tags": ["taught"],
            "success_count": 3,
            "steps": [
                {"type": "click", "x": 440, "y": 210, "window_title": "Inbox - Microsoft Outlook"},
                {"type": "type_text", "text": "password=hunter2 secret invoice"},
                {"type": "keystroke", "key": "a"},
            ],
        }
        (duties / "morning_email.json").write_text(json.dumps(payload), encoding="utf-8")
        Path(self.root, "storage", "agent.md").write_text(
            "## Lessons\n- failed: C:\\Secrets\\ledger.xlsx missing window\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_sanitize_steps_are_types_only(self):
        types = sanitize_steps(
            [{"type": "click", "x": 1, "y": 2}, {"type": "type_text", "text": "hi"}]
        )
        self.assertEqual(types, ["click", "type_text"])

    def test_distillate_strips_payloads_and_secrets(self):
        packet = build_skill_distillate(
            self.root, install_id="id-1", version="0.1.8", reason="launch"
        )
        blob = json.dumps(packet)
        self.assertNotIn("440", blob)
        self.assertNotIn("hunter2", blob)
        self.assertNotIn("user@example.com", blob)
        self.assertNotIn("C:\\Secrets", blob)
        self.assertIn("[REDACTED_PATH]", blob)
        self.assertEqual(packet["duty_count"], 1)
        self.assertEqual(packet["duties"][0]["step_types"], ["click", "type_text", "keystroke"])
        self.assertEqual(packet["duties"][0]["app_families"], ["outlook"])
        self.assertEqual(packet["privacy"], "no_documents_no_keystrokes_no_screens_no_inventory")

    def test_distillate_excludes_internal_catalog(self):
        catalog = Path(self.root, "storage", "internal_data")
        catalog.mkdir(parents=True)
        (catalog / "sample_availability.csv").write_text(
            "name,country,price\nHotel Roma,Italy,EUR 120\nSECRET_INVENTORY_ROW,Italy,999\n",
            encoding="utf-8",
        )
        Path(self.root, "storage", "agent.md").write_text(
            "## Lessons\n- Internal catalog Hotel Roma EUR 120 SECRET_INVENTORY_ROW\n"
            "- failed: Outlook window missing after send\n",
            encoding="utf-8",
        )
        packet = build_skill_distillate(self.root, install_id="id-1", version="0.1.8")
        blob = json.dumps(packet)
        self.assertNotIn("SECRET_INVENTORY_ROW", blob)
        self.assertNotIn("EUR 120", blob)
        self.assertTrue(any("Outlook window missing" in x for x in packet["lessons"]))


if __name__ == "__main__":
    unittest.main()
