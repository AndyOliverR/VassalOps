import os
import sys
import re
import time

class VassalOpsMemoryExtractor:
    """Memory Extractor Loop: Context engineers and extracts preference rules from raw natural language chat turns [0:1.95, 0:1.306]."""
    def __init__(self, memory_path: str = "storage/agent.md"):
        self.memory_path = memory_path
        print("[VassalOps Memory] Ambient Context Memory Extractor active [0:1.242, 0:1.286].")

    def analyze_chat_for_memory_update(self, user_feedback: str) -> bool:
        """Parses human feedback turns to dynamically update agent.md memory configurations [0:1.296, 0:1.308]."""
        cleaned_text = user_feedback.lower().strip()
        print(f" [Memory Extractor] Parsing natural language text turn stream: '{user_feedback}' [0:1.95]")
        
        updated_rule = None
        if "ignore" in cleaned_text and "low" in cleaned_text:
            updated_rule = "- IGNORE_ANOMALIES_UNDER_SEVERITY: Low\n"
        elif "latency" in cleaned_text or "delay" in cleaned_text:
            updated_rule = "- AUTO_LATENCY_DELAY_PADDING: Enabled due to coordinate bounding drift trends.\n"
            
        if updated_rule and os.path.exists(self.memory_path):
            with open(self.memory_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Prevent duplicating existing configuration rules inside memory documentation
            if updated_rule.strip() not in content:
                with open(self.memory_path, "a", encoding="utf-8") as f:
                    f.write(f"\n# Updated from Conversational Feedback ({time.strftime('%Y-%m-%d')})\n{updated_rule}")
                print(f" [Memory Extractor] Success: Preference rule append-injected directly into agent.md [0:1.286].")
                return True
                
        print(" [Memory Extractor] Pass complete. No persistent rule alterations required.")
        return False

if __name__ == "__main__":
    extractor = VassalOpsMemoryExtractor()
    extractor.analyze_chat_for_memory_update("Please ignore low priority issues, they are annoying.")
