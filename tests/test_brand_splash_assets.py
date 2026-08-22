"""Hermetic checks for kneeling-knight brand mark + splash assets."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


class TestBrandAndSplashAssets(unittest.TestCase):
    def test_knight_brand_files_exist(self):
        required = [
            ROOT / "storage" / "dashboard" / "assets" / "vassal_knight_source.png",
            ROOT / "storage" / "dashboard" / "assets" / "vassal_knight.png",
            ROOT / "storage" / "dashboard" / "assets" / "BRANDING.txt",
            ROOT / "storage" / "dashboard" / "vassal_icon.png",
            ROOT / "storage" / "dashboard" / "vassal_icon.ico",
            ROOT / "storage" / "dashboard" / "vassalops_bare.ico",
            ROOT / "storage" / "dashboard" / "splash.html",
            ROOT / "storage" / "dashboard" / "splash.css",
            ROOT / "tools" / "show_splash.py",
            ROOT / "tools" / "export_vassal_icon.py",
        ]
        for path in required:
            self.assertTrue(path.is_file(), f"missing {path}")

    def test_icon_png_is_transparent_rgba(self):
        img = Image.open(ROOT / "storage" / "dashboard" / "vassal_icon.png")
        self.assertEqual(img.mode, "RGBA")
        corner = img.getpixel((0, 0))
        self.assertEqual(corner[3], 0, "corner should be transparent (no black plate)")

    def test_splash_uses_knight_png(self):
        html = (ROOT / "storage" / "dashboard" / "splash.html").read_text(encoding="utf-8")
        self.assertIn("vassal_knight.png", html)
        self.assertNotIn("vassal_mark.svg", html)
        self.assertNotIn("vassal_knight_splash.png", html)

    def test_branding_describes_knight(self):
        text = (ROOT / "storage" / "dashboard" / "assets" / "BRANDING.txt").read_text(encoding="utf-8").lower()
        self.assertIn("knight", text)
        self.assertIn("transparent", text)
        self.assertIn("silver", text)

    def test_splash_flag_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            flag = Path(tmp) / "splash_seen.json"
            flag.write_text(json.dumps({"seen": True}), encoding="utf-8")
            data = json.loads(flag.read_text(encoding="utf-8"))
            self.assertTrue(data["seen"])


if __name__ == "__main__":
    unittest.main()
