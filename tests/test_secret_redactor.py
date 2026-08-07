import unittest
from src.ingestion.secret_redactor import redact_secrets


class TestSecretRedactor(unittest.TestCase):
    def test_redacts_email(self):
        out = redact_secrets("contact me at user@example.com please")
        self.assertIn("[REDACTED_EMAIL]", out)
        self.assertNotIn("user@example.com", out)

    def test_redacts_sk_key(self):
        out = redact_secrets("token sk-abcdefghijklmnopqrstuvwxyz")
        self.assertIn("[REDACTED_API_KEY]", out)

    def test_redacts_bearer(self):
        out = redact_secrets("Authorization Bearer abcdefghijklmnop")
        self.assertIn("[REDACTED_TOKEN]", out)

    def test_redacts_password_kv(self):
        out = redact_secrets("password=hunter2")
        self.assertIn("password=[REDACTED]", out)
        self.assertNotIn("hunter2", out)

    def test_redacts_long_digits(self):
        out = redact_secrets("card 4111111111111111")
        self.assertIn("[REDACTED_DIGITS]", out)


if __name__ == "__main__":
    unittest.main()
