import re
import json

class GMInputParser:
    def __init__(self, max_chars=4000):
        self.max_chars = max_chars
        self.malicious_patterns = [
            re.compile(r"ignore\s+previous\s+instructions", re.IGNORECASE),
            re.compile(r"system\s+override", re.IGNORECASE),
            re.compile(r"you\s+are\s+now\s+an\s+unfiltered", re.IGNORECASE)
        ]

    def sanitize_text(self, text: str) -> str:
        """Strip dangerous characters and block prompt injection strings."""
        if not text:
            return ""
        
        clean_text = text[:self.max_chars]
        
        for pattern in self.malicious_patterns:
            if pattern.search(clean_text):
                raise ValueError("Security Boundary Violated: Prompt injection detected.")
                
        return clean_text.strip()

    def parse_payload(self, raw_payload: str) -> dict:
        """Normalize raw incoming payload telemetry data, escaping system paths safely."""
        try:
            # If it's already a string, clean up backslashes so json.loads doesn't crash on \ windows paths
            if isinstance(raw_payload, str):
                # Only fix raw prompts that aren't valid JSON yet
                if not (raw_payload.strip().startswith('{') and raw_payload.strip().endswith('}')):
                    raw_payload = raw_payload.replace("\\", "\\\\")
            
            data = json.loads(raw_payload) if isinstance(raw_payload, str) else raw_payload
            processed_prompt = self.sanitize_text(data.get("prompt", ""))
            return {
                "status": "CLEAN",
                "prompt": processed_prompt,
                "metadata": data.get("metadata", {})
            }
        except ValueError as ve:
            return {"status": "BLOCKED", "error": str(ve), "prompt": ""}
        except Exception as e:
            return {"status": "MALFORMED", "error": f"Invalid payload schema: {str(e)}", "prompt": ""}

