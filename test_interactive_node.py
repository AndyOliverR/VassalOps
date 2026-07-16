import sys
import os
import webview
import json
import threading

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from orchestrator import GMAIEngine

class VassalOpsWebGUI:
    def __init__(self):
        self.engine = GMAIEngine()
        self.session_id = "sandbox_developer_session"
        
    def start(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(base_dir, 'storage', 'dashboard', 'index.html')
        
        # Open a gorgeous, fluid, modern hardware-accelerated desktop window
        self.window = webview.create_window(
            title="VassalOps",
            url=html_path,
            width=950,
            height=720,
            resizable=True,
            background_color='#0f172a'
        )
        webview.start(self.bind_bridge, debug=False)
        
    def bind_bridge(self):
        # Expose Python backend tasks to our glossy HTML interface smoothly
        self.window.expose(self.dispatch_to_engine)
        
    def dispatch_to_engine(self, user_prompt):
        # Stream response back to the front-end layout
        raw_payload = json.dumps({"prompt": user_prompt})
        full_response = ""
        for token in self.engine.process_message(self.session_id, raw_payload):
            full_response += token
            # Dynamically push tokens straight to our web text stream console
            self.window.evaluate_js(f"appendTokenToStream({json.dumps(token)});")

if __name__ == "__main__":
    app = VassalOpsWebGUI()
    app.start()