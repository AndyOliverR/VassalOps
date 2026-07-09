import sys
import os
import json
import time

# Dynamically ensure top-level project module access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

class VassalOpsJobTrainer:
    def __init__(self, storage_dir: str = "storage/job_roles/"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        print("[GM AI Trainer] Job Role Cognitive Training Layer initialized.")

    def ingest_job_description(self, role_name: str, raw_jd_text: str) -> str:
        """Parses raw job descriptions and extracts structured actionable skills for the AI."""
        cleaned_role = role_name.lower().strip().replace(" ", "_")
        profile_path = os.path.join(self.storage_dir, f"{cleaned_role}_profile.json")

        # Basic keyword parsing rules to discover required peripheral tools dynamically
        tools_discovered = []
        jd_lower = raw_jd_text.lower()
        
        if "browser" in jd_lower or "chrome" in jd_lower or "web" in jd_lower:
            tools_discovered.append("chrome")
        if "notepad" in jd_lower or "text" in jd_lower or "documentation" in jd_lower:
            tools_discovered.append("notepad")
        if "terminal" in jd_lower or "cmd" in jd_lower or "command" in jd_lower:
            tools_discovered.append("command_prompt")

        # Build the structural cognitive asset profile
        role_profile = {
            "role_title": role_name,
            "trained_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "required_system_tools": tools_discovered,
            "raw_capabilities_context": raw_jd_text[:1000] # Cap text limits cleanly
        }

        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(role_profile, f, indent=2)
            
        print(f"[GM AI Trainer] Successfully compiled cognitive role map for: {role_name}")
        return profile_path

if __name__ == "__main__":
    trainer = VassalOpsJobTrainer()
    print("[GM AI] Running local job ingestion validation test...")
    
    # Sample Mock Job Description input for testing
    sample_title = "Data Entry Assistant"
    sample_jd = "Looking for an assistant to open Chrome, navigate web listings, and type text data logs into Notepad."
    
    path = trainer.ingest_job_description(sample_title, sample_jd)
    print(f"[GM AI] Job profile successfully generated at: {path}")


