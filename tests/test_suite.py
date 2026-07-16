import unittest
import urllib.request
import json

class TestVassalOpsPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = "127.0.0.1"
        cls.port = 11434
        cls.model_name = "gpt-oss:120b-cloud"
        cls.base_url = f"http://{cls.host}:{cls.port}"

    def test_01_server_alive(self):
        """Verify the local Ollama daemon endpoint responds."""
        url = f"{self.base_url}/api/tags"
        try:
            response = urllib.request.urlopen(url, timeout=5)
            self.assertEqual(response.getcode(), 200)
        except Exception as e:
            self.fail(f"Ollama server is unreachable: {e}")

    def test_02_model_presence(self):
        """Verify gpt-oss:120b-cloud is present in local inventory."""
        url = f"{self.base_url}/api/tags"
        response = urllib.request.urlopen(url, timeout=5)
        data = json.loads(response.read().decode('utf-8'))
        models = [m['name'] for m in data.get('models', [])]
        self.assertIn(self.model_name, models, f"Model {self.model_name} not found.")

    def test_03_futureseer_network_baseline(self):
        """Production Check: Verify live network scraping pipeline against FutureSeer.app."""
        target_url = "https://www.futureseer.app"
        req = urllib.request.Request(
            target_url, 
            headers={'User-Agent': 'Mozilla/5.0 GM-AI-Core-Network-Validator/1.0'}
        )
        try:
            with urllib.request.urlopen(req, timeout=7) as response:
                status_code = response.getcode()
                # Confirm the website is alive and serving healthy 200 response codes
                self.assertEqual(status_code, 200, f"FutureSeer.app returned status {status_code}")
        except Exception as e:
            self.fail(f"Live network verification test failed to reach FutureSeer.app: {e}")

if __name__ == "__main__":
    unittest.main()

