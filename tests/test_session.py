import unittest
import os
import shutil
import sys
sys.path.append(r'C:\VassalOps\src')
from tracking.session import GMSessionTracker

class TestGMSessionTracker(unittest.TestCase):
    def setUp(self):
        self.test_dir = r"C:\VassalOps\storage_test"
        self.tracker = GMSessionTracker(storage_dir=self.test_dir, max_history=2)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_session_creation_and_append(self):
        sid = "user_test_123"
        self.tracker.append_turn(sid, "user", "Hello Engine")
        history = self.tracker.load_history(sid)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["content"], "Hello Engine")

    def test_memory_cap_truncation(self):
        sid = "limit_test"
        # Append 6 turns (exceeds our max_history * 2 space limit)
        for i in range(6):
            self.tracker.append_turn(sid, "user" if i%2==0 else "assistant", f"Turn {i}")
        history = self.tracker.load_history(sid)
        self.assertEqual(len(history), 4) # Hard restricted back to 4 elements max
        self.assertEqual(history[-1]["content"], "Turn 5")

if __name__ == "__main__":
    unittest.main()


