"""Hermetic tests for version compare + overlay apply."""
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

from src.execution.product_update import apply_extracted_update, is_newer_version, parse_version


class TestProductUpdate(unittest.TestCase):
    def test_is_newer_version(self):
        self.assertTrue(is_newer_version("0.1.8", "0.1.7"))
        self.assertFalse(is_newer_version("0.1.7", "0.1.7"))
        self.assertFalse(is_newer_version("0.1.6", "0.1.7"))
        self.assertEqual(parse_version("v1.2.3-beta"), (1, 2, 3))

    def test_apply_preserves_duties_and_config(self):
        tmp = tempfile.TemporaryDirectory()
        root = tmp.name
        src = Path(tmp.name, "_src")
        src.mkdir()
        (src / "app.py").write_text("new-app\n", encoding="utf-8")
        (src / "VERSION").write_text("9.9.9", encoding="utf-8")
        (src / "config.json").write_text("{}", encoding="utf-8")
        dash = src / "storage" / "dashboard"
        packs = src / "storage" / "duties" / "packs"
        dash.mkdir(parents=True)
        packs.mkdir(parents=True)
        (dash / "index.html").write_text("new-ui", encoding="utf-8")
        (packs / "demo.json").write_text("{}", encoding="utf-8")

        Path(root, "app.py").write_text("old-app\n", encoding="utf-8")
        Path(root, "VERSION").write_text("0.1.0", encoding="utf-8")
        Path(root, "config.json").write_text(json.dumps({"keep": True}), encoding="utf-8")
        Path(root, "storage", "duties").mkdir(parents=True)
        Path(root, "storage", "duties", "taught.json").write_text("{}", encoding="utf-8")
        Path(root, "storage", "dashboard").mkdir(parents=True)
        Path(root, "storage", "dashboard", "index.html").write_text("old-ui", encoding="utf-8")

        apply_extracted_update(str(src), root, "9.9.9")

        self.assertEqual(Path(root, "app.py").read_text(encoding="utf-8"), "new-app\n")
        self.assertEqual(Path(root, "VERSION").read_text(encoding="utf-8"), "9.9.9")
        cfg = json.loads(Path(root, "config.json").read_text(encoding="utf-8"))
        self.assertTrue(cfg["keep"])
        self.assertTrue(Path(root, "storage", "duties", "taught.json").is_file())
        self.assertEqual(Path(root, "storage", "dashboard", "index.html").read_text(encoding="utf-8"), "new-ui")
        tmp.cleanup()

    def test_apply_preserves_existing_config_local(self):
        tmp = tempfile.TemporaryDirectory()
        root = tmp.name
        src = Path(tmp.name, "_src")
        src.mkdir()
        (src / "app.py").write_text("new-app\n", encoding="utf-8")
        (src / "config.local.json").write_text(json.dumps({"runtime_boundaries": {"registration_github_token": "from-zip"}}), encoding="utf-8")
        Path(root, "app.py").write_text("old-app\n", encoding="utf-8")
        Path(root, "config.json").write_text("{}", encoding="utf-8")
        Path(root, "config.local.json").write_text(json.dumps({"runtime_boundaries": {"registration_github_token": "keep-me"}}), encoding="utf-8")
        Path(root, "storage").mkdir()
        apply_extracted_update(str(src), root, "9.9.9")
        local = json.loads(Path(root, "config.local.json").read_text(encoding="utf-8"))
        self.assertEqual(local["runtime_boundaries"]["registration_github_token"], "keep-me")
        tmp.cleanup()

    def test_apply_adopts_config_local_when_missing(self):
        tmp = tempfile.TemporaryDirectory()
        root = tmp.name
        src = Path(tmp.name, "_src")
        src.mkdir()
        (src / "app.py").write_text("new-app\n", encoding="utf-8")
        (src / "config.local.json").write_text(json.dumps({"runtime_boundaries": {"registration_github_token": "from-zip"}}), encoding="utf-8")
        Path(root, "app.py").write_text("old-app\n", encoding="utf-8")
        Path(root, "config.json").write_text("{}", encoding="utf-8")
        Path(root, "storage").mkdir()
        apply_extracted_update(str(src), root, "9.9.9")
        local = json.loads(Path(root, "config.local.json").read_text(encoding="utf-8"))
        self.assertEqual(local["runtime_boundaries"]["registration_github_token"], "from-zip")
        tmp.cleanup()


class TestInjectReleaseToken(unittest.TestCase):
    def test_inject_writes_env_token(self):
        tmp = tempfile.TemporaryDirectory()
        dest = Path(tmp.name, "config.local.json")
        script = Path(__file__).resolve().parents[1] / "tools" / "inject_release_token.py"
        spec = importlib.util.spec_from_file_location("inject_release_token", script)
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        old = os.environ.get("VASSALOPS_INSTALLS_PAT")
        os.environ["VASSALOPS_INSTALLS_PAT"] = "ghp_ci_inject_test"
        try:
            code = mod.main([str(dest)])
            self.assertEqual(code, 0)
            data = json.loads(dest.read_text(encoding="utf-8"))
            self.assertEqual(
                data["runtime_boundaries"]["registration_github_token"],
                "ghp_ci_inject_test",
            )
        finally:
            if old is None:
                os.environ.pop("VASSALOPS_INSTALLS_PAT", None)
            else:
                os.environ["VASSALOPS_INSTALLS_PAT"] = old
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
