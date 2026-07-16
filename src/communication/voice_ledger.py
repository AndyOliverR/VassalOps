import sys
import os
import sqlite3
import time

# Dynamically ensure top-level project module access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

try:
    import pyttsx3
except ImportError:
    raise ImportError("Dependency missing. Please run: pip install pyttsx3")

class VassalOpsVoiceAuditor:
    def __init__(self, db_path: str = "gm_memory.db"):
        self.db_path = db_path
        # Initialize text-to-speech engine canvas
        self.speech_engine = pyttsx3.init()
        # Set realistic human speech rhythm pacing parameter
        self.speech_engine.setProperty('rate', 155)

    def speak_timeline_summary(self):
        """Queries the latest historical ledger rows and narrates transaction audit sequences out loud."""
        if not os.path.exists(self.db_path):
            self._announce("Warning. Persistent state ledger database missing.")
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if the audit table exists before running calculations
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_action_audit'")
        if not cursor.fetchone():
            self._announce("No system interaction audit table established inside memory yet.")
            conn.close()
            return

        cursor.execute("SELECT id, device_source, command_intent, execution_status FROM system_action_audit ORDER BY id DESC LIMIT 3")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            narrative = "GM A.I. ledger timeline is currently empty. No automated actions have been recorded yet."
            print(f"[VassalOps Audio] Narrating: {narrative}")
            self._announce(narrative)
            return

        total_count = len(rows)
        narrative = f"Initializing audio summary ledger grid sequence. Found latest {total_count} transactions recorded inside system timeline memory. "
        
        for idx, row in enumerate(rows, 1):
            device = row[1]
            intent = row[2]
            status = row[3].replace('_', ' ')
            narrative += f"Transaction record number {idx}. Dispatched via device, {device}. Action command intent requested was, {intent}. Resulting status was, {status}. "

        print(f"[VassalOps Audio] Narrating: {narrative}")
        self._announce(narrative)

    def _announce(self, text: str):
        self.speech_engine.say(text)
        self.speech_engine.runAndWait()

if __name__ == "__main__":
    auditor = VassalOpsVoiceAuditor()
    print("[VassalOps] Initializing Voice Auditing Node test matrix tracker...")
    auditor.speak_timeline_summary()




