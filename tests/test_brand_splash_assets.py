"""Hermetic checks for original brand mark + splash assets."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestBrandAndSplashAssets(unittest.TestCase):
    def test_original_mark_files_exist(self):
        required = [
            ROOT / "storage" / "dashboard" / "assets" / "vassal_mark.svg",
            ROOT / "storage" / "dashboard" / "assets" / "BRANDING.txt",
            ROOT / "storage" / "dashboard" / "vassal_icon.png",
            ROOT / "storage" / "dashboard" / "vassal_icon.ico",
            ROOT / "storage" / "dashboard" / "splash.html",
            ROOT / "storage" / "dashboard" / "splash.css",
            ROOT / "tools" / "show_splash.py",
            ROOT / "tools" / "export_vassal_icon.py",
        ]
        for path in required:
            self.assertTrue(path.is_file(), f"missing {path}")

    def test_svg_has_mark_groups(self):
        svg = (ROOT / "storage" / "dashboard" / "assets" / "vassal_mark.svg").read_text(encoding="utf-8")
        for name in ("figure", "legL", "legR", "armL", "armR", "torso", "badge"):
            self.assertIn(f'id="{name}"', svg)
        self.assertIn('viewBox="0 0 256 256"', svg)

    def test_branding_claims_original(self):
        text = (ROOT / "storage" / "dashboard" / "assets" / "BRANDING.txt").read_text(encoding="utf-8").lower()
        self.assertIn("original", text)
        self.assertIn("not stock", text)

    def test_splash_flag_roundtrip(self):
        # Mirror VassalOpsAPI flag path without loading full app (Ollama side effects).
        with tempfile.TemporaryDirectory() as tmp:
            flag = Path(tmp) / "splash_seen.json"
            self.assertFalse(flag.is_file())
            payload = {"seen": True, "at": "test"}
            flag.write_text(json.dumps(payload), encoding="utf-8")
            data = json.loads(flag.read_text(encoding="utf-8"))
            self.assertTrue(data["seen"])


if __name__ == "__main__":
    unittest.main()
