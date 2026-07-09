import sqlite3
import os
from datetime import datetime

class GMDatabaseManager:
    def __init__(self, db_path=r"C:\VassalOps\storage\gm_core.db"):
        self.db_path = db_path
        # Ensure directory paths exist before initiating connections
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._initialize_tables()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _initialize_tables(self):
        """Build explicit relation schemas for core sessions, action steps, and events."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Table 1: Conversational Log Store
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            
            # Table 2: Automation Launch Log Store
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS action_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    app_key TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.commit()

    def log_message(self, session_id: str, role: str, content: str):
        """Insert a conversation log entry with explicit ISO string timestamps."""
        timestamp = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_history (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, role, content, timestamp)
            )
            conn.commit()

    def log_action(self, session_id: str, app_key: str, status: str):
        """Log the execution status of local automation steps."""
        timestamp = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO action_logs (session_id, app_key, status, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, app_key, status, timestamp)
            )
            conn.commit()

    def get_session_history(self, session_id: str, limit=10) -> list:
        """Fetch historical conversation logs ordered by timestamp parameters."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content FROM chat_history WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit)
            )
            rows = cursor.fetchall()
            # Reverse order to restore historical progression sequence flow
            return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

