import json
import os

class GMSessionTracker:
    def __init__(self, storage_dir=r"C:\VassalOps\storage", max_history=5):
        self.storage_dir = storage_dir
        self.max_history = max_history
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)

    def _get_session_path(self, session_id: str) -> str:
        return os.path.join(self.storage_dir, f"session_{session_id}.json")

    def load_history(self, session_id: str) -> list:
        """Retrieve recent conversation turns for context initialization."""
        file_path = self._get_session_path(session_id)
        if not os.path.exists(file_path):
            return []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def append_turn(self, session_id: str, role: str, content: str) -> list:
        """Add a conversation turn and truncate if history exceeds memory caps."""
        history = self.load_history(session_id)
        history.append({"role": role, "content": content})
        
        # Keep only the most recent turns to protect VRAM boundaries
        if len(history) > (self.max_history * 2):
            history = history[-(self.max_history * 2):]
            
        file_path = self._get_session_path(session_id)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)
        return history

