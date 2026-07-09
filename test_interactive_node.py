import sys
import os
import json
import tkinter as tk
from tkinter import scrolledtext
import threading

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from orchestrator import GMAIEngine
from telemetry.sensor import GMTelemetrySensor

class GMAIGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("VassalOps Core Engine Workspace")
        self.root.geometry("800x650")
        self.root.configure(bg="#1e1e24")
        
        self.engine = GMAIEngine()
        self.sensor = GMTelemetrySensor()
        self.session_id = "sandbox_developer_session"
        
        self.create_widgets()
        
    def create_widgets(self):
        title_label = tk.Label(
            self.root, 
            text="VassalOps Core Engine Workspace (Operator: Bot-Sitter)", 
            font=("Arial", 14, "bold"), fg="#ffffff", bg="#1e1e24", pady=10
        )
        title_label.pack(fill=tk.X)
        
        self.chat_display = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state=tk.DISABLED, 
            font=("Consolas", 11), bg="#2d2d34", fg="#ffffff", insertbackground="white"
        )
        self.chat_display.pack(padx=15, pady=10, fill=tk.BOTH, expand=True)
        
        self.append_text("SYSTEM", "Visual UI Console active. Type 'status' to poll telemetry or 'exit' to quit.")
        self.append_text("AUDIO", "Voice command modules active. Prefix voice text simulation entries with 'voice '.")
        self.append_text("SYSTEM", "-"*60 + "\n")
        
        # Bottom controls container
        controls_frame = tk.Frame(self.root, bg="#1e1e24")
        controls_frame.pack(fill=tk.X, padx=15, pady=15, side=tk.BOTTOM)
        
        self.entry_field = tk.Entry(
            controls_frame, font=("Arial", 12), bg="#3e3e42", fg="#ffffff", insertbackground="white"
        )
        self.entry_field.pack(fill=tk.X, side=tk.LEFT, expand=True, ipady=4)
        self.entry_field.bind("<Return>", lambda event: self.send_message())
        
        # Voice Command simulation button trigger
        voice_btn = tk.Button(
            controls_frame, text="🎙️ Sim Voice", font=("Arial", 11, "bold"),
            bg="#28a745", fg="#ffffff", activebackground="#1e7e34", activeforeground="white",
            command=self.simulate_voice_input, width=12
        )
        voice_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        send_btn = tk.Button(
            controls_frame, text="Execute", font=("Arial", 11, "bold"), 
            bg="#007acc", fg="#ffffff", activebackground="#005999", activeforeground="white",
            command=self.send_message, width=12
        )
        send_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
    def append_text(self, sender, text):
        self.chat_display.configure(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{sender}: {text}\n")
        self.chat_display.see(tk.END)
        self.chat_display.configure(state=tk.DISABLED)
        
    def simulate_voice_input(self):
        """Simulate a raw local microphone voice transcription hook activation."""
        self.entry_field.delete(0, tk.END)
        self.entry_field.insert(0, "voice open config")
        self.append_text("MIC LISTEN", "[Listening...] Caught voice frequency shortcut trigger.")
        self.root.after(800, self.send_message)

    def send_message(self):
        user_input = self.entry_field.get().strip()
        if not user_input:
            return
            
        self.entry_field.delete(0, tk.END)
        
        # Audio preprocessing handler: strip hotword signals
        if user_input.lower().startswith("voice "):
            clean_voice_prompt = user_input[6:].strip()
            self.append_text("Bot-Sitter (Voice)", clean_voice_prompt)
            user_input = clean_voice_prompt
        else:
            self.append_text("Bot-Sitter", user_input)
        
        if user_input.lower() in ['exit', 'quit']:
            self.append_text("SYSTEM", "Closing engine workspace window session...")
            self.root.after(1000, self.root.destroy)
            return
            
        if user_input.lower() == 'status':
            report = self.sensor.format_telemetry_report()
            self.append_text("GM AI Engine", f"\n{report}\n")
            return
            
        threading.Thread(target=self.stream_engine_response, args=(user_input,), daemon=True).start()
        
    def stream_engine_response(self, prompt):
        self.append_text("GM AI Engine", "")
        raw_payload = json.dumps({"prompt": prompt})
        
        for token in self.engine.process_message(self.session_id, raw_payload):
            self.chat_display.configure(state=tk.NORMAL)
            self.chat_display.insert(tk.END, token)
            self.chat_display.see(tk.END)
            self.chat_display.configure(state=tk.DISABLED)
        
        self.chat_display.configure(state=tk.NORMAL)
        self.chat_display.insert(tk.END, "\n")
        self.chat_display.configure(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = GMAIGUI(root)
    root.mainloop()


