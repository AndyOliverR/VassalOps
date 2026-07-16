import json
import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger("GMSemanticMatcher")

class GMSemanticMatcher:
    def __init__(self, catalog_path: str = "C:\\VassalOps\\ai-catalog.json"):
        self.catalog_path = catalog_path
        self.capabilities = []
        self.load_catalog()

    def load_catalog(self):
        try:
            with open(self.catalog_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
                self.capabilities = data.get("capabilities", [])
        except Exception as e:
            print(f"[CATALOG ERROR] Failed to ingest AI capability catalog: {str(e)}")
            self.capabilities = []

    def clean_tokens(self, text: str) -> set:
        normalized = text.lower().strip()
        tokens = re.findall(r'[a-z0-9]+', normalized)
        return set(tokens)

    def extract_intent(self, user_input: str) -> Optional[Dict[str, Any]]:
        user_tokens = self.clean_tokens(user_input)
        if not user_tokens:
            return None

        best_match = None
        highest_score = 0

        for cap in self.capabilities:
            for phrasing in cap.get("phrasings", []):
                phrase_tokens = self.clean_tokens(phrasing)
                intersection = user_tokens.intersection(phrase_tokens)
                score = len(intersection)

                if score > highest_score:
                    highest_score = score
                    best_match = cap

        if highest_score > 0:
            return best_match
        return None

if __name__ == "__main__":
    matcher = GMSemanticMatcher()
    # Test our new capability with broken phrasing
    test_run = matcher.extract_intent("hey run safe script test please")
    print(f"[TEST COMPLETED] Matched capability ID: {test_run['id'] if test_run else 'None'}")


