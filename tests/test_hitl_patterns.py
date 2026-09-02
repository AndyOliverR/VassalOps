import os
import tempfile
import unittest

from src.execution.risk_tiers import risk_summary, tool_risk
from src.execution.run_evidence import write_run_report
from src.execution.local_learning import append_unique_bullets, record_loop_outcome
from src.execution.session_store import save_last_session, load_last_session, format_resume_context
from src.execution.action_firewall import VassalOpsActionFirewall


class TestRiskTiers(unittest.TestCase):
    def test_read_vs_desktop(self):
        self.assertEqual(tool_risk("list_duties"), "read")
        self.assertEqual(tool_risk("search_memory"), "read")
        self.assertEqual(tool_risk("search_internal"), "read")
        self.assertEqual(tool_risk("read_internal_sheet"), "desktop")
        self.assertEqual(tool_risk("type_text"), "desktop")
        self.assertEqual(tool_risk("agent_loop"), "desktop")
        summary = risk_summary([{"type": "speak_log", "payload": "hi"}, {"type": "run_duty", "payload": "x"}])
        self.assertTrue(summary["has_desktop"])
        self.assertIn("Desktop tools", summary["message"])


class TestRunEvidence(unittest.TestCase):
    def test_redacts_and_writes(self):
        tmp = tempfile.mkdtemp(prefix="vo_runs_")
        path = write_run_report(
            goal="email user@example.com",
            ok=False,
            turns=2,
            observations=["password=hunter2 failed"],
            final="nope",
            reason="window missing",
            runs_dir=tmp,
        )
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        self.assertIn("[REDACTED_EMAIL]", text)
        self.assertIn("[REDACTED]", text)
        self.assertIn("FAIL", text)


class TestLocalLearning(unittest.TestCase):
    def test_dedupe(self):
        tmp = os.path.join(tempfile.mkdtemp(prefix="vo_learn_"), "agent.md")
        os.makedirs(os.path.dirname(tmp), exist_ok=True)
        n1 = append_unique_bullets(tmp, "## Lessons", ["failed: window missing"])
        n2 = append_unique_bullets(tmp, "## Lessons", ["failed: window missing"])
        self.assertEqual(n1, 1)
        self.assertEqual(n2, 0)
        record_loop_outcome(tmp, {"ok": False, "reason": "Window SAP not found", "observations": []}, goal="sap")
        with open(tmp, "r", encoding="utf-8") as f:
            body = f.read()
        self.assertIn("## Preferences", body)
        self.assertIn("skip if window missing", body)


class TestSessionStore(unittest.TestCase):
    def test_roundtrip(self):
        path = os.path.join(tempfile.mkdtemp(prefix="vo_sess_"), "last.json")
        save_last_session(goal="open notepad", observations=["typed hello"], final="done", ok=True, path=path)
        data = load_last_session(path)
        self.assertEqual(data["goal"], "open notepad")
        ctx = format_resume_context(data)
        self.assertIn("Prior goal", ctx)
        self.assertIn("Approve", ctx)


class TestDeniedHotkeys(unittest.TestCase):
    def test_alt_f4_blocked(self):
        fw = VassalOpsActionFirewall()
        self.assertEqual(fw.verify_step({"type": "press_hotkey", "payload": "alt+f4"})["status"], "REJECTED")
        self.assertEqual(fw.verify_step({"type": "press_hotkey", "payload": "ctrl+s"})["status"], "VERIFIED")


if __name__ == "__main__":
    unittest.main()
