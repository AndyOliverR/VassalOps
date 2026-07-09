import sys
import os
import subprocess
import time
from typing import Optional

class GMAIAppBootstrapper:
    def __init__(self):
        self.app_registry = {
            "notepad": r"C:\Windows\System32\notepad.exe",
            "calc": r"C:\Windows\System32\calc.exe",
            "cmd": r"C:\Windows\System32\cmd.exe",
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "chrome_x86": r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        }
        print("[GM AI Bootstrapper] Web and process registry initialized.")

    def _locate_binary_globally(self, binary_name: str) -> Optional[str]:
        search_roots = [
            os.environ.get("PROGRAMFILES", r"C:\Program Files"),
            os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
            os.environ.get("WINDIR", r"C:\Windows"),
            os.environ.get("LOCALAPPDATA", "")
        ]
        search_roots = [r for r in search_roots if r]
        filename = f"{binary_name}.exe"
        print(f"[GM AI Bootstrapper] Self-Healing engaged: Searching Windows paths for '{filename}'...")
        
        for root in search_roots:
            if not os.path.exists(root):
                continue
            for subfolder in ["Google\\Chrome\\Application", "System32", ""]:
                check_dir = os.path.join(root, subfolder)
                target_path = os.path.join(check_dir, filename)
                if os.path.exists(target_path):
                    return target_path
        return None

    def ensure_application_running(self, app_name: str) -> bool:
        """Checks if an application process is active. If not, boots it dynamically with crash diagnostics."""
        app_key = app_name.lower().strip()
        search_process = "chrome" if "chrome" in app_key else app_key

        try:
            tasklist_check = subprocess.check_output(f'tasklist /FI "IMAGENAME eq {search_process}.exe"', shell=True).decode('utf-8', errors='ignore')
            if f"{search_process}.exe" in tasklist_check.lower():
                print(f"[GM AI Bootstrapper] Active process detected for '{search_process}'. No boot required.")
                return True
        except Exception:
            pass

        exe_path = None
        if "chrome" in app_key:
            if os.path.exists(self.app_registry["chrome"]): exe_path = self.app_registry["chrome"]
            elif os.path.exists(self.app_registry["chrome_x86"]): exe_path = self.app_registry["chrome_x86"]
            else: exe_path = self._locate_binary_globally("chrome")
        elif app_key in self.app_registry and os.path.exists(self.app_registry[app_key]):
            exe_path = self.app_registry[app_key]
        else:
            exe_path = self._locate_binary_globally(app_key)

        if exe_path and os.path.exists(exe_path):
            print(f"[GM AI Bootstrapper] Spawning executable target path: {exe_path}")
            
            try:
                # Spawn target process and capture the internal process hook reference
                proc = subprocess.Popen(exe_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Active diagnostics verification window to catch early startup failure crashes
                time.sleep(0.5)
                poll_status = proc.poll()
                
                # If poll returns a returncode value instead of remaining None, an early crash happened
                if poll_status is not None and poll_status != 0:
                    print(f"[GM AI Diagnostic Alert] Spelled process '{app_key}' crashed on boot. ReturnCode: {poll_status}")
                    return False
                    
                print(f"[GM AI Bootstrapper] Subprocess initialization verified healthy. PID tracked: {proc.pid}")
                time.sleep(1.5 if "chrome" in app_key else 1.0)
                return True
                
            except Exception as e:
                print(f"[GM AI Diagnostic Error] Critical OS failure spawning subprocess thread: {e}")
                return False

        print(f"[GM AI Bootstrapper] Error: Failed to resolve stable target path for '{app_key}'.")
        return False

if __name__ == "__main__":
    bootstrapper = GMAIAppBootstrapper()
    print("[GM AI] Running browser boot validation check...")
    bootstrapper.ensure_application_running("chrome")


