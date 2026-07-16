import sys
import os
import webview
import json
import threading
import base64

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from orchestrator import GMAIEngine

class APIBridge:
    def __init__(self, engine, session_id, window):
        self.engine = engine
        self.session_id = session_id
        self.window = window

    def dispatch_to_engine(self, user_prompt):
        threading.Thread(target=self._run_engine, args=(user_prompt,), daemon=True).start()

    def _run_engine(self, user_prompt):
        raw_payload = json.dumps({"prompt": user_prompt})
        for token in self.engine.process_message(self.session_id, raw_payload):
            escaped_token = json.dumps(token)
            self.window.evaluate_js(f"window.appendTokenToStream({escaped_token});")
        self.window.evaluate_js("window.finalizeStream();")

    def get_base64_image(self, file_path):
        """Converts any selected file directly into a secure text string to bypass security walls."""
        if not file_path or not os.path.exists(file_path):
            return ""
        try:
            ext = os.path.splitext(file_path)[1].lower().replace('.', '')
            if ext == 'jpg': ext = 'jpeg'
            with open(file_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                return f"data:image/{ext};base64,{encoded_string}"
        except Exception as e:
            print(f"[VassalOps Base64 Error] Failed to encode image: {e}")
            return ""

class VassalOpsWebGUI:
    def __init__(self):
        self.engine = GMAIEngine()
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
