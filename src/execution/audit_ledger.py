import os
import sqlite3
import time

class GMAIAuditLedger:
    def __init__(self, db_path: str = "gm_memory.db"):
        self.db_path = db_path
        self._initialize_audit_table()

    def _initialize_audit_table(self):
        """Creates or alters the system action audit ledger schema to enforce channel isolation properties."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Base schema initialization with integrated session channel tracking properties
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_action_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    channel_id TEXT NOT NULL DEFAULT 'default_channel',
                    device_source TEXT NOT NULL,
                    command_intent TEXT NOT NULL,
                    execution_status TEXT NOT NULL
                )
            ''')
            
            # Self-healing migration checking patch loop to add column safely to older setups
            cursor.execute("PRAGMA table_info(system_action_audit)")
            columns = [col[1] for col in cursor.fetchall()]
            if "channel_id" not in columns:
                print("[GM AI Ledger] Schema migration engaged: Appending structural channel_id matrix tracking field...")
                cursor.execute("ALTER TABLE system_action_audit ADD COLUMN channel_id TEXT NOT NULL DEFAULT 'default_channel'")
                
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[GM AI Ledger Error] Failed to initialize table structures: {e}")

    def commit_transaction(self, intent: str, status: str = "success_completed", device: str = "local_desktop", channel: str = "main_session"):
        """Commits a high-frequency automation transaction row bound directly to a user partition channel."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            timestamp = int(time.time())
            
            cursor.execute('''
                INSERT INTO system_action_audit (timestamp, channel_id, device_source, command_intent, execution_status)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, channel, device, intent, status))
            
            conn.commit()
            conn.close()
            print(f"[GM AI Ledger] Committed transaction line on channel '{channel}' for intent: '{intent}'")
            return True
        except Exception as e:
            print(f"[GM AI Ledger Error] Failed to write historical row artifact: {e}")
            return False

if __name__ == "__main__":
    print("[INIT] Testing Phase 15 Partitioned AuditLedger pipelines...")
    ledger = GMAIAuditLedger()
    ledger.commit_transaction(intent="verify channel isolation partitioning bounds", status="AUDITED", channel="device_alpha_node")


