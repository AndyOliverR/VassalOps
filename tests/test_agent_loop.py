import json
import os
import tempfile
import unittest

from src.execution.agent_loop import parse_loop_decision, run_agent_loop
from src.execution.agent_tools import search_memory, truncate_messages, execute_loop_tool
from src.execution.duty_library import VassalOpsDutyLibrary


class TestParseLoopDecision(unittest.TestCase):
    def test_tool_call(self):
        d = parse_loop_decision({"action": "tool_call", "name": "list_duties", "payload": ""})
        self.assertEqual(d["kind"], "tool_call")
        self.assertEqual(d["name"], "list_duties")

    def test_final(self):
        d = parse_loop_decision('{"action":"final","payload":"Done."}')
        self.assertEqual(d["kind"], "final")
        self.assertEqual(d["payload"], "Done.")

    def test_invalid(self):
        d = parse_loop_decision("not json")
        self.assertEqual(d["kind"], "invalid")


class TestTruncateMessages(unittest.TestCase):
    def test_keeps_system_user_and_newest(self):
        messages = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "goal"},
            {"role": "observation", "content": "x" * 200},
            {"role": "observation", "content": "recent"},
        ]
        out = truncate_messages(messages, max_chars=40)
        self.assertEqual(out[0]["role"], "system")
        self.assertEqual(out[1]["role"], "user")
        self.assertEqual(out[-1]["content"], "recent")
        self.assertTrue(any("summarized" in (m.get("content") or "") for m in out) or len(out) <= 4)


class TestSearchMemory(unittest.TestCase):
    def test_keyword_hits_duty(self):
        tmp = tempfile.mkdtemp(prefix="vassal_mem_")
        lib = VassalOpsDutyLibrary(duties_dir=tmp)
        path = os.path.join(tmp, "morning_email.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"id": "morning_email", "name": "Morning Email", "steps": [], "success_count": 0}, f)
        md = os.path.join(tmp, "agent.md")
        with open(md, "w", encoding="utf-8") as f:
            f.write("Prefer extra latency when Outlook is slow.\n")
        text = search_memory("email", duty_library=lib, agent_md_path=md)
        self.assertIn("morning_email", text)


class TestExecuteLoopTool(unittest.TestCase):
    def test_rejects_unknown(self):
        result = execute_loop_tool("shell_exec", "rm")
        self.assertFalse(result["ok"])

    def test_speak_log(self):
        result = execute_loop_tool("speak_log", "hello")
        self.assertTrue(result["ok"])
        self.assertEqual(result["observation"], "hello")


class TestAgentLoop(unittest.TestCase):
    def test_final_on_first_turn(self):
        report = run_agent_loop(
            "say hi",
            call_model=lambda _p: {"action": "final", "payload": "Hello."},
            execute_tool=lambda n, p: {"ok": True, "observation": "unused"},
            max_turns=8,
        )
        self.assertTrue(report["ok"])
        self.assertEqual(report["final"], "Hello.")
        self.assertEqual(report["turns"], 1)

    def test_tool_then_final(self):
        calls = {"n": 0}

        def model(_p):
            calls["n"] += 1
            if calls["n"] == 1:
                return {"action": "tool_call", "name": "speak_log", "payload": "working"}
            return {"action": "final", "payload": "All set."}

        def exec_tool(name, payload):
            return {"ok": True, "observation": f"ran {name}:{payload}"}

        report = run_agent_loop("demo", call_model=model, execute_tool=exec_tool, max_turns=8)
        self.assertTrue(report["ok"])
        self.assertEqual(report["turns"], 2)
        self.assertTrue(any("speak_log" in o for o in report["observations"]))

    def test_max_turns(self):
        report = run_agent_loop(
            "forever",
            call_model=lambda _p: {"action": "tool_call", "name": "speak_log", "payload": "again"},
            execute_tool=lambda n, p: {"ok": True, "observation": "ok"},
            max_turns=3,
        )
        self.assertFalse(report["ok"])
        self.assertEqual(report["turns"], 3)
        self.assertIn("max_turns", report["reason"])

    def test_stop(self):
        report = run_agent_loop(
            "x",
            call_model=lambda _p: {"action": "final", "payload": "nope"},
            execute_tool=lambda n, p: {"ok": True, "observation": "ok"},
            stop_requested=lambda: True,
        )
        self.assertTrue(report["stopped"])
        self.assertFalse(report["ok"])


if __name__ == "__main__":
    unittest.main()
