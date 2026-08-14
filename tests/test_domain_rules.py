import unittest

from src.execution.agent_loop import run_agent_loop
from src.execution.domain_rules import check_tool_result, domain_prompt_block


class TestDomainRules(unittest.TestCase):
    def test_prompt_names_entities(self):
        text = domain_prompt_block()
        self.assertIn("Duty", text)
        self.assertIn("Window", text)
        self.assertIn("Approve", text)

    def test_rejects_shell_tool(self):
        out = check_tool_result("shell_exec", {"ok": True, "observation": "ran"})
        self.assertFalse(out["ok"])
        self.assertIn("shell_", out["note"])

    def test_rejects_unknown_tool(self):
        out = check_tool_result("invented_click", {"ok": False, "observation": "nope"})
        self.assertFalse(out["ok"])
        self.assertIn("not a workday tool", out["note"])

    def test_focus_window_missing(self):
        out = check_tool_result("focus_window", {"ok": False, "observation": "Window 'Foo' not found."})
        self.assertFalse(out["ok"])
        self.assertIn("Window entity missing", out["note"])

    def test_run_duty_missing(self):
        out = check_tool_result("run_duty", {"ok": False, "observation": "Duty morning_email not found"})
        self.assertFalse(out["ok"])
        self.assertIn("taught Duty", out["note"])

    def test_list_duties_empty_is_ok_with_note(self):
        out = check_tool_result("list_duties", {"ok": True, "observation": "No duties taught yet."})
        self.assertTrue(out["ok"])
        self.assertIn("empty", out["note"].lower())

    def test_speak_log_clean(self):
        out = check_tool_result("speak_log", {"ok": True, "observation": "hello"})
        self.assertTrue(out["ok"])
        self.assertEqual(out["note"], "")


class TestDomainNoteInLoop(unittest.TestCase):
    def test_observation_includes_domain_note(self):
        report = run_agent_loop(
            "focus notepad",
            call_model=lambda _p: {"action": "tool_call", "name": "focus_window", "payload": "Nope"},
            execute_tool=lambda n, p: {"ok": False, "observation": "Window 'Nope' not found."},
            max_turns=1,
        )
        self.assertTrue(any("Window entity missing" in o for o in report["observations"]))


if __name__ == "__main__":
    unittest.main()
