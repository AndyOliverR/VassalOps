import unittest
import sys
sys.path.append(r'C:\VassalOps\src')
from actions.bridge import GMActionBridge

class TestGMActionBridge(unittest.TestCase):
    def setUp(self):
        self.bridge = GMActionBridge()

    def test_whitelist_validation(self):
        """Verify the internal application whitelisting checks function properly."""
        # Check an item explicitly listed in our whitelist key paths
        self.assertIn("calc", self.bridge.allowed_applications)
        self.assertIn("notepad", self.bridge.allowed_applications)

    def test_unauthorized_app_blocked(self):
        """Verify dangerous or unauthorized keys are rejected cleanly."""
        result = self.bridge.execute_app("powershell.exe")
        self.assertEqual(result["status"], "REJECTED")

if __name__ == "__main__":
    unittest.main()


