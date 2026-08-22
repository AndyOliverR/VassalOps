"""Hermetic tests for ICM-inspired staged packs + Spice needs_you brief."""
from __future__ import annotations

import os
import tempfile
import threading
import time
import unittest

from src.execution.duty_library import VassalOpsDutyLibrary
from src.execution.run_controller import VassalOpsRunController
from src.execution.staged_pack import (
    format_needs_you_brief,
    import_staged_packs,
    load_pack_manifest,
    resolve_pack_dir,
    run_staged_pack,
)


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPO_PACK = os.path.join(ROOT, "storage", "duties", "packs", "staged_demo_notepad")


class TestStagedPackLayout(unittest.TestCase):
    def test_repo_staged_pack_exists(self):
        self.assertTrue(os.path.isdir(REPO_PACK), "staged_demo_notepad pack missing")
        self.assertTrue(os.path.isfile(os.path.join(REPO_PACK, "pack.json")))
        self.assertTrue(os.path.isfile(os.path.join(REPO_PACK, "01_open_notepad", "CONTEXT.md")))
        self.assertTrue(os.path.isfile(os.path.join(REPO_PACK, "01_open_notepad", "duty.json")))
        self.assertTrue(os.path.isfile(os.path.join(REPO_PACK, "02_type_greeting", "duty.json")))

    def test_manifest_loads(self):
        m = load_pack_manifest(REPO_PACK)
        self.assertEqual(m["kind"], "staged_pack")
        self.assertEqual(len(m["stages"]), 2)
        self.assertTrue(m["stages"][0].get("approve_after"))


class TestStagedPackImport(unittest.TestCase):
    def test_import_staged_into_temp_library(self):
        tmp = tempfile.mkdtemp(prefix="vassal_staged_")
        packs = os.path.join(tmp, "packs", "staged_demo_notepad")
        os.makedirs(packs)
        # Minimal copy of repo pack structure
        import json
        import shutil

        shutil.copytree(
            REPO_PACK,
            packs,
            dirs_exist_ok=True,
        )
        lib = VassalOpsDutyLibrary(duties_dir=tmp)
        result = import_staged_packs(lib)
        self.assertTrue(result["ok"], result.get("error"))
        self.assertIn("staged_demo_notepad", result["imported_packs"])
        self.assertTrue(lib.get_duty("staged_demo_notepad_01_open"))
        self.assertTrue(lib.get_duty("staged_demo_notepad_02_type"))
        self.assertIsNotNone(resolve_pack_dir(tmp, "staged_demo_notepad"))


class TestNeedsYouBrief(unittest.TestCase):
    def test_format(self):
        text = format_needs_you_brief(shipped="a", stuck="b", needs_you="Approve stage 2")
        self.assertIn("Shipped: a", text)
        self.assertIn("Needs you: Approve stage 2", text)

    def test_controller_parses_needs_you(self):
        c = VassalOpsRunController()
        c.set_summary(format_needs_you_brief(needs_you="Approve to continue"))
        self.assertEqual(c.snapshot()["needs_you"], "Approve to continue")


class TestStageGatePause(unittest.TestCase):
    def test_gate_sets_pending_replan(self):
        """First stage approve_after pauses; confirm_replan resumes without desktop replay."""
        tmp = tempfile.mkdtemp(prefix="vassal_gate_")
        packs = os.path.join(tmp, "packs", "mini")
        os.makedirs(os.path.join(packs, "01_a", "output"), exist_ok=True)
        os.makedirs(os.path.join(packs, "02_b", "output"), exist_ok=True)
        import json

        with open(os.path.join(packs, "pack.json"), "w", encoding="utf-8") as f:
            json.dump(
                {
                    "id": "mini",
                    "kind": "staged_pack",
                    "stages": [
                        {
                            "folder": "01_a",
                            "name": "A",
                            "duty_id": "mini_a",
                            "approve_after": True,
                        },
                        {
                            "folder": "02_b",
                            "name": "B",
                            "duty_id": "mini_b",
                            "approve_after": False,
                        },
                    ],
                },
                f,
            )
        for folder, did in (("01_a", "mini_a"), ("02_b", "mini_b")):
            with open(os.path.join(packs, folder, "CONTEXT.md"), "w", encoding="utf-8") as f:
                f.write("# test\n")
            with open(os.path.join(packs, folder, "duty.json"), "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "id": did,
                        "name": did,
                        "steps": [{"type": "wait", "seconds": 0.01, "delay": 0.0}],
                    },
                    f,
                )

        lib = VassalOpsDutyLibrary(duties_dir=tmp)
        self.assertTrue(import_staged_packs(lib)["ok"])
        # MacroPlayer always reads under ./storage/; stub replay for hermetic gate test
        lib.run_duty = lambda duty_id: {"ok": True, "duty_id": duty_id, "name": duty_id}
        ctrl = VassalOpsRunController()

        def _approve_soon() -> None:
            time.sleep(0.2)
            # Wait until paused with pending_replan
            for _ in range(50):
                snap = ctrl.snapshot()
                if snap.get("pending_replan"):
                    ctrl.confirm_replan()
                    return
                time.sleep(0.05)

        t = threading.Thread(target=_approve_soon, daemon=True)
        t.start()
        report = run_staged_pack("mini", library=lib, run_controller=ctrl)
        t.join(timeout=5)
        self.assertTrue(report.get("ok"), report)
        self.assertEqual(len(report.get("results") or []), 2)


if __name__ == "__main__":
    unittest.main()
