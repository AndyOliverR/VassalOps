import logging

logger = logging.getLogger("GMHarnessValidator")

class GMHarnessValidator:
    def __init__(self):
        # Define foundational system blacklists to prevent arbitrary system bricking
        self.payload_blacklist = ["rmdir /s", "del /f", "format ", "drop database"]

    def verify_action(self, target_command: str) -> dict:
        """Adversarial loop inspecting generated actions before runtime deployment."""
        normalized_cmd = target_command.lower().strip()

        # Check against destructive commands
        for blacklisted in self.payload_blacklist:
            if blacklisted in normalized_cmd:
                return {
                    "status": "REJECTED",
                    "reason": f"Security boundary violation: Found dangerous instruction '{blacklisted}'"
                }

        # Check for empty payloads
        if not normalized_cmd:
            return {
                "status": "REJECTED",
                "reason": "Execution harness payload is empty."
            }

        return {
            "status": "VERIFIED",
            "reason": "Payload matches capability safety rules."
        }

if __name__ == "__main__":
    validator = GMHarnessValidator()
    test_fail = validator.verify_action("del /f /q C:\\windows")
    test_pass = validator.verify_action("open config")
    print(f"[HARNESS TEST] Malicious Command: {test_fail['status']} (Reason: {test_fail['reason']})")
    print(f"[HARNESS TEST] Valid Command: {test_pass['status']}")

