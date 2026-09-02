"""Hermetic tests for local PIN gate + GitHub installs notepad."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from src.execution.local_auth import (
    LocalAuthSession,
    load_merged_config,
    load_profile,
    maybe_register_pending,
    try_github_issue_register,
    try_oneshot_register,
)


class TestLocalAuth(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        Path(self.root, "VERSION").write_text("9.9.9", encoding="utf-8")
        Path(self.root, "config.json").write_text(
            json.dumps({"runtime_boundaries": {"registration_endpoint": ""}}),
            encoding="utf-8",
        )
        self.auth = LocalAuthSession(root=self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_signup_unlock_and_hashes(self):
        result = self.auth.signup(
            "user@example.com",
            "1234",
            "What city were you born in?",
            "Boston",
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["unlocked"])
        self.assertTrue(self.auth.unlocked)

        profile = load_profile(self.root)
        self.assertIsNotNone(profile)
        raw = Path(self.root, "storage", "auth", "profile.json").read_text(encoding="utf-8")
        self.assertNotIn("1234", raw)
        self.assertNotIn("Boston", raw)
        self.assertNotIn("boston", raw)
        self.assertIn("pin_hash", profile)
        self.assertIn("answer_hash", profile)
        self.assertEqual(profile["email"], "user@example.com")

        self.auth.lock()
        self.assertFalse(self.auth.unlocked)
        bad = self.auth.unlock("9999")
        self.assertFalse(bad["ok"])
        good = self.auth.unlock("1234")
        self.assertTrue(good["ok"])

    def test_reset_pin_with_secret(self):
        self.auth.signup("a@b.co", "1111", "What was your first school?", "Lincoln")
        self.auth.lock()
        fail = self.auth.reset_pin("wrong", "2222")
        self.assertFalse(fail["ok"])
        ok = self.auth.reset_pin("Lincoln", "2222")
        self.assertTrue(ok["ok"])
        self.auth.lock()
        self.assertTrue(self.auth.unlock("2222")["ok"])
        self.assertFalse(self.auth.unlock("1111")["ok"])

    def test_covenant_requires_sponsor_star_and_rating(self):
        self.auth.signup("lab@b.co", "1234", "City?", "Pune")
        denied = self.auth.complete_covenant(sponsored=False, starred=True, rating="5")
        self.assertFalse(denied["ok"])
        ok = self.auth.complete_covenant(sponsored=True, starred=True, rating="5")
        self.assertTrue(ok["ok"])
        profile = load_profile(self.root)
        self.assertTrue(profile["covenant"]["sponsored_claimed"])
        self.assertEqual(profile["covenant"]["rating"], "5")
        status = self.auth.status()
        self.assertTrue(status["covenant_complete"])

    def test_https_endpoint_ping_mocked(self):
        resp = MagicMock()
        resp.status_code = 200

        def fake_post(url, json=None, headers=None, timeout=8.0):
            self.assertEqual(url, "https://example.test/register")
            self.assertEqual(json["email"], "x@y.z")
            self.assertEqual(json["app"], "VassalOps")
            return resp

        ok, msg = try_oneshot_register(
            email="x@y.z",
            install_id="id-1",
            version="1.0",
            endpoint="https://example.test/register",
            post=fake_post,
        )
        self.assertTrue(ok)
        self.assertIn("sent", msg.lower())

    def test_github_issue_notepad_mocked(self):
        resp = MagicMock()
        resp.status_code = 201
        captured = {}

        def fake_post(url, json=None, headers=None, timeout=8.0):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers or {}
            return resp

        ok, msg = try_github_issue_register(
            email="user@example.com",
            install_id="uuid-1",
            version="0.1.7",
            repo="AndyOliverR/vassalops-installs",
            token="ghp_test_token",
            post=fake_post,
        )
        self.assertTrue(ok)
        self.assertIn("github", msg.lower())
        self.assertEqual(captured["url"], "https://api.github.com/repos/AndyOliverR/vassalops-installs/issues")
        self.assertEqual(captured["json"]["title"], "install: user@example.com")
        self.assertIn("user@example.com", captured["json"]["body"])
        self.assertIn("uuid-1", captured["json"]["body"])
        self.assertIn("Bearer ghp_test_token", captured["headers"].get("Authorization", ""))

    def test_config_local_merge_for_token(self):
        Path(self.root, "config.json").write_text(
            json.dumps(
                {
                    "runtime_boundaries": {
                        "registration_github_repo": "AndyOliverR/vassalops-installs",
                        "registration_github_token": "",
                    }
                }
            ),
            encoding="utf-8",
        )
        Path(self.root, "config.local.json").write_text(
            json.dumps({"runtime_boundaries": {"registration_github_token": "secret_pat"}}),
            encoding="utf-8",
        )
        merged = load_merged_config(self.root)
        rb = merged["runtime_boundaries"]
        self.assertEqual(rb["registration_github_repo"], "AndyOliverR/vassalops-installs")
        self.assertEqual(rb["registration_github_token"], "secret_pat")

    def test_maybe_register_pending_idempotent(self):
        Path(self.root, "config.json").write_text(
            json.dumps(
                {
                    "runtime_boundaries": {
                        "registration_github_repo": "owner/repo",
                        "registration_github_token": "tok",
                    }
                }
            ),
            encoding="utf-8",
        )
        self.auth.signup("z@z.co", "1234", "City?", "Pune")
        # Force unregistered
        profile = load_profile(self.root)
        self.assertIsNotNone(profile)
        profile["registered_at"] = None
        Path(self.root, "storage", "auth", "profile.json").write_text(
            json.dumps(profile), encoding="utf-8"
        )

        resp = MagicMock()
        resp.status_code = 201
        calls = []

        def fake_post(url, json=None, headers=None, timeout=8.0):
            calls.append(url)
            return resp

        first = maybe_register_pending(self.root, post=fake_post)
        self.assertTrue(first["ok"])
        self.assertFalse(first["skipped"])
        self.assertEqual(len(calls), 1)

        second = maybe_register_pending(self.root, post=fake_post)
        self.assertTrue(second["skipped"])
        self.assertEqual(second["reason"], "already_registered")
        self.assertEqual(len(calls), 1)

    def test_no_endpoint_still_creates_account(self):
        out = self.auth.signup("offline@test.com", "4444", "City?", "Delhi")
        self.assertTrue(out["ok"])
        self.assertFalse(out["registered"])
        self.assertIn("local only", out["registration"].lower())

    def test_template_config_has_empty_token(self):
        root = Path(__file__).resolve().parents[1]
        cfg = json.loads((root / "config.json").read_text(encoding="utf-8"))
        token = (cfg.get("runtime_boundaries") or {}).get("registration_github_token", "MISSING")
        self.assertEqual(token, "")
        example = (root / "config.local.json.example").read_text(encoding="utf-8")
        self.assertIn("PASTE_FINE_GRAINED_PAT_HERE", example)
        self.assertNotIn("ghp_", example)

    def test_release_workflow_injects_secret_not_git_token(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        self.assertIn("config.local.json", workflow)
        self.assertIn("VASSALOPS_INSTALLS_PAT", workflow)
        self.assertIn("--exclude='config.local.json'", workflow)
        self.assertIn("tools/inject_release_token.py", workflow)


if __name__ == "__main__":
    unittest.main()
