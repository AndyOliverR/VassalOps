import subprocess
import socket
import time
import os

class VassalOpsOllamaGuard:
    def __init__(self, port: int = 11434):
        self.port = port
        self.host = "127.0.0.1"

    def is_server_online(self) -> bool:
        """Performs a lightweight local network socket ping test to check availability."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1.5)
                s.connect((self.host, self.port))
                return True
        except (socket.timeout, ConnectionRefusedError):
            return False

    def ensure_service_active(self) -> bool:
        """Checks service health and background spawns the host process if offline."""
        if self.is_server_online():
            print("[VassalOps Guard] Ollama inference engine detected ONLINE and healthy.")
            return True

        print("[WARN] Ollama engine is offline. Attempting to start daemon process automatically...")
        
        try:
            # Spawns Ollama into a quiet background thread without locking up the terminal window
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Allow localized engine warm up delays
            for attempt in range(1, 6):
                time.sleep(1.5)
                if self.is_server_online():
                    print(f"[OK] Ollama server daemon successfully initialized after {attempt * 1.5}s.")
                    return True
                print(f" [!] Waiting for server socket connection to initialize... (Attempt {attempt}/5)")
                
        except FileNotFoundError:
            print("[VassalOps Guard Error] 'ollama' executable missing from system environment PATH.")
            return False

        print("[VassalOps Guard Error] Failed to verify safe connection to Ollama cluster.")
        return False

if __name__ == "__main__":
    guard = VassalOpsOllamaGuard()
    guard.ensure_service_active()
