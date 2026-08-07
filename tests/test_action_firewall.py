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

    def test_rejects_multipart_press_key(self):
        result = self.fw.verify_step({"type": "press_key", "payload": "ctrl a"})
        self.assertEqual(result["status"], "REJECTED")


if __name__ == "__main__":
    unittest.main()
