import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from actions.bridge import GMActionBridge


class TestGMActionBridge(unittest.TestCase):
    def setUp(self):
        self.bridge = GMActionBridge()

    def test_whitelist_validation(self):
        """Verify the internal application whitelisting checks function properly."""
        self.assertIn("calc", self.bridge.allowed_applications)
        self.assertIn("notepad", self.bridge.allowed_applications)

    def test_unauthorized_app_blocked(self):
        """Verify dangerous or unauthorized keys are rejected cleanly."""
        result = self.bridge.execute_app("powershell.exe")
        self.assertEqual(result["status"], "REJECTED")


if __name__ == "__main__":
    unittest.main()
