import sys
import os
import webview
import json
import threading
import http.client
import importlib

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Clean dynamic loader: Inspects your files natively without hardcoding legacy names
EngineClass = None
SensorClass = None

try:
    orch_mod = importlib.import_module("orchestrator")
    # Dynamically find whatever class is exported inside orchestrator
    for attr_name in dir(orch_mod):
        if "Engine" in attr_name:
            EngineClass = getattr(orch_mod, attr_name)
            break
except Exception:
    pass

if not EngineClass:
    class EngineClass:
        def process_message(self, s_id, payload): return ["Engine offline..."]

try:
    sensor_mod = importlib.import_module("telemetry.sensor")
    for attr_name in dir(sensor_mod):
        if "Sensor" in attr_name:
            SensorClass = getattr(sensor_mod, attr_name)
            break
except Exception:
    pass

if not SensorClass:
    class SensorClass:
        def format_telemetry_report(self): return "Sensor metrics offline."

# Import your native automation engine modules using the clean VassalOps prefix
try:
    from execution.macro_recorder import VassalOpsMacroRecorder
    from execution.macro_player import VassalOpsMacroPlayer
except ImportError:
    class VassalOpsMacroRecorder:
        def start_recording(self): pass
        def stop_recording(self): return []
    class VassalOpsMacroPlayer:
        def execute_replay(self, steps): pass

class APIBridge:
    def __init__(self, engine, session_id, window):
        self.engine = engine
        self.session_id = session_id
        self.window = window
        
        # Local workspace safe storage setup
        self.memory_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'storage')
        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)
        self.library_path = os.path.join(self.memory_dir, 'learned_keywords.json')
        
        # Active automation controllers with corrected project definitions
        self.recorder = VassalOpsMacroRecorder()
        self.player = VassalOpsMacroPlayer()
        self.is_recording = False
        self.current_recording_keyword = ""
        
        self.keywords = self._load_keywords()

    def _load_keywords(self):
        if os.path.exists(self.library_path):
            try:
                with open(self.library_path, 'r') as f:
                    return json.load(f)
            except Exception: pass
        return {
            "signin": {"desc": "Prepares login focus paths.", "steps": []},
            "signout": {"desc": "Clears active connection frames.", "steps": []}
        }

    def _save_keywords(self):
        try:
            with open(self.library_path, 'w') as f:
                json.dump(self.keywords, f, indent=4)
        except Exception: pass

    def check_ollama_status(self):
        try:
            conn = http.client.HTTPConnection("127.0.0.1", 11434, timeout=2)
            conn.request("GET", "/api/tags")
            res = conn.getresponse()
            if res.status == 200: return True
        except Exception: pass
        return False
    def dispatch_to_engine(self, user_prompt):
        threading.Thread(target=self._run_engine, args=(user_prompt,), daemon=True).start()

    def _run_engine(self, user_prompt):
        clean_input = user_prompt.strip()
        lower_input = clean_input.lower()

        # Handle Macro Recording Toggles
        if lower_input == "stop" and self.is_recording:
            self.is_recording = False
            recorded_steps = self.recorder.stop_recording()
            kw = self.current_recording_keyword
            self.keywords[kw]["steps"] = recorded_steps
            self._save_keywords()
            msg = f"✅ **Recording Finished!** I have saved all clicks and keys into keyword: **`{kw}`**."
            self.window.evaluate_js(f"window.appendTokenToStream({json.dumps(msg)});")
            self.window.evaluate_js("window.finalizeStream();")
            return

        if self.is_recording:
            msg = "⚠️ I am currently recording your actions. Type **`stop`** to finish mapping this keyword sequence."
            self.window.evaluate_js(f"window.appendTokenToStream({json.dumps(msg)});")
            self.window.evaluate_js("window.finalizeStream();")
            return

        # Keyword learning handler setup block
        if lower_input.startswith("learn "):
            parts = clean_input.split(" ", 2)
            if len(parts) >= 2:
                kw = parts[1].lower()
                desc = parts[2] if len(parts) > 2 else "User configured automation task."
                
                self.keywords[kw] = {"desc": desc, "steps": []}
                self.is_recording = True
                self.current_recording_keyword = kw
                self.recorder.start_recording()
                
                msg = f"🎙️ **Learning Mode Triggered!** Go ahead and perform the task on your PC normally.<br>I am recording your mouse and keyboard moves for **`{kw}`**.<br>When you are done, type **`stop`** right here to lock in the skill."
                self.window.evaluate_js(f"window.appendTokenToStream({json.dumps(msg)});")
            self.window.evaluate_js("window.finalizeStream();")
            return

        # Live Real-Time Automation Replay Execution Block
        if lower_input in self.keywords:
            task = self.keywords[lower_input]
            msg = f"🐕 **Fetching and Performing Task:** `[ {lower_input} ]`... Running macro automation sequence: *{task['desc']}*"
            self.window.evaluate_js(f"window.appendTokenToStream({json.dumps(msg)});")
            
            # Execute real physical mouse moves and layout clicks on the PC natively
            if task.get("steps"):
                threading.Thread(target=self.player.execute_replay, args=(task["steps"],), daemon=True).start()
                
            self.window.evaluate_js("window.finalizeStream();")
            return

        # Fallback to local Ollama server status checks
        if not self.check_ollama_status():
            guide = "⚠️ **Ollama engine is offline on this PC!** Connect via terminal or type a learned keyword shortcut."
            self.window.evaluate_js(f"window.appendTokenToStream({json.dumps(guide)});")
            self.window.evaluate_js("window.finalizeStream();")
            return

        # Normal AI pipeline response channel route
        raw_payload = json.dumps({"prompt": clean_input})
        for token in self.engine.process_message(self.session_id, raw_payload):
            self.window.evaluate_js(f"window.appendTokenToStream({json.dumps(token)});")
        self.window.evaluate_js("window.finalizeStream();")

class VassalOpsWebGUI:
    def __init__(self):
        self.engine = EngineClass()
        self.sensor = SensorClass()
        self.session_id = "sandbox_developer_session"
        
    def start(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(base_dir, 'storage', 'dashboard', 'index.html')
        icon_file_path = os.path.join(base_dir, 'app_icon.ico')
        
        self.window = webview.create_window(
            title="VassalOps",
            url=html_path,
            width=950,
            height=720,
            resizable=True,
            background_color='#1A202C'
        )
        
        api = APIBridge(self.engine, self.session_id, self.window)
        self.window.api = api
        
        storage_path = os.path.join(os.environ.get('APPDATA', ''), 'VassalOps', 'webview_cache')
        webview.start(icon=icon_file_path, debug=False, private_mode=False, storage_path=storage_path, http_server=True)

if __name__ == "__main__":
    app = VassalOpsWebGUI()
    app.start()
