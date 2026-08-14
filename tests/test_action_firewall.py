import unittest
from src.execution.action_firewall import VassalOpsActionFirewall


class TestActionFirewall(unittest.TestCase):
    def setUp(self):
        self.fw = VassalOpsActionFirewall()

    def test_allows_type_text(self):
        result = self.fw.verify_step({"type": "type_text", "payload": "hello"})
        self.assertEqual(result["status"], "VERIFIED")

    def test_rejects_unknown_type(self):
        result = self.fw.verify_step({"type": "shell_exec", "payload": "rm -rf /"})
        self.assertEqual(result["status"], "REJECTED")

    def test_rejects_bad_click_payload(self):
        result = self.fw.verify_step({"type": "click_element", "payload": "notepad"})
        self.assertEqual(result["status"], "REJECTED")

    def test_allows_click_payload(self):
        result = self.fw.verify_step({"type": "click_element", "payload": "notepad.save"})
        self.assertEqual(result["status"], "VERIFIED")

    def test_allows_learn_macro(self):
        result = self.fw.verify_step({"type": "learn_macro", "payload": "demo.json"})
        self.assertEqual(result["status"], "VERIFIED")

    def test_allows_teach_and_playlist(self):
        self.assertEqual(self.fw.verify_step({"type": "teach_duty", "payload": "email"} )["status"], "VERIFIED")
        self.assertEqual(self.fw.verify_step({"type": "run_duty", "payload": "email"} )["status"], "VERIFIED")
        self.assertEqual(self.fw.verify_step({"type": "run_playlist", "payload": "today"} )["status"], "VERIFIED")

    def test_allows_agent_loop_and_memory(self):
        self.assertEqual(self.fw.verify_step({"type": "agent_loop", "payload": "summarize in notepad"})["status"], "VERIFIED")
        self.assertEqual(self.fw.verify_step({"type": "search_memory", "payload": "email"})["status"], "VERIFIED")
        self.assertEqual(self.fw.verify_step({"type": "list_duties", "payload": ""})["status"], "VERIFIED")
        self.assertEqual(self.fw.verify_step({"type": "agent_loop", "payload": ""})["status"], "REJECTED")

    def test_rejects_multipart_press_key(self):
        result = self.fw.verify_step({"type": "press_key", "payload": "ctrl+c"})
        self.assertEqual(result["status"], "REJECTED")


if __name__ == "__main__":
    unittest.main()
