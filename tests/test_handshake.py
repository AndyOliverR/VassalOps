"""Hermetic tests for lab-rat handshake send path."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from src.execution.handshake import run_handshake, send_skill_update
from src.execution.local_auth import LocalAuthSession, load_profile, save_profile


class TestHandshake(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        Path(self.root, "VERSION").write_text("0.1.8", encoding="utf-8")
        Path(self.root, "config.json").write_text(
            json.dumps(
                {
                    "runtime_boundaries": {
                        "registration_github_repo": "AndyOliverR/vassalops-installs",
                        "registration_github_token": "",
                    },
                    "handshake": {
                        "enabled": True,
                        "product_repo": "AndyOliverR/VassalOps",
                        "learn_repo": "AndyOliverR/vassalops-installs",
                    },
                }
            ),
            encoding="utf-8",
        )
        Path(self.root, "storage", "duties").mkdir(parents=True)
        (Path(self.root, "storage", "duties") / "inbox.json").write_text(
            json.dumps({"id": "inbox", "tags": ["taught"], "steps": [{"type": "click", "x": 9, "y": 9}]}),
            encoding="utf-8",
        )
        self.auth = LocalAuthSession(root=self.root)
        self.auth.signup("lab@example.com", "1234", "City?", "Pune")
        Path(self.root, "config.json").write_text(
            json.dumps(
                {
                    "runtime_boundaries": {
                        "registration_github_repo": "AndyOliverR/vassalops-installs",
                        "registration_github_token": "tok",
                    },
                    "handshake": {
                        "enabled": True,
                        "product_repo": "AndyOliverR/VassalOps",
                        "learn_repo": "AndyOliverR/vassalops-installs",
                    },
                }
            ),
            encoding="utf-8",
        )
        profile = load_profile(self.root)
        profile["github_issue_number"] = 7
        save_profile(profile, self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_send_skipped_without_profile(self):
        auth_dir = Path(self.root, "storage", "auth")
        for p in auth_dir.glob("*.json"):
            p.unlink()
        result = send_skill_update(self.root, reason="launch")
        self.assertTrue(result["skipped"])
        self.assertEqual(result["reason"], "no_profile")

    def test_send_without_covenant(self):
        captured = {}

        def fake_post(url, json=None, headers=None, timeout=8.0):
            captured["url"] = url
            captured["json"] = json
            resp = MagicMock()
            resp.status_code = 201
            resp.json.return_value = {"id": 1}
            return resp

        result = send_skill_update(self.root, reason="launch", post=fake_post)
        self.assertTrue(result["ok"])
        self.assertIn("/issues/7/comments", captured["url"])
        body = captured["json"]["body"]
        self.assertNotIn('"x": 9', body)
        self.assertIn("skill_distillate", body)
        self.assertIn("inbox", body)

    def test_run_handshake_skips_network_product_check_when_get_mocked(self):
        os.environ["VASSALOPS_SKIP_UPDATE"] = "1"

        def fake_post(url, json=None, headers=None, timeout=8.0):
            resp = MagicMock()
            resp.status_code = 201
            resp.json.return_value = {"id": 1, "number": 7}
            return resp

        try:
            out = run_handshake(reason="launch", root=self.root, apply_product=False, post=fake_post)
            self.assertTrue(out["ok"])
            self.assertIn("SKIP_UPDATE", out["received"]["message"])
        finally:
            os.environ.pop("VASSALOPS_SKIP_UPDATE", None)


if __name__ == "__main__":
    unittest.main()
