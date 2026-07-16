import urllib.request
import json
import re

class GMNetworkScraper:
    def fetch_live_text(self, url: str) -> str:
        """Fetch content from a secure public URL, stripping HTML noise or nesting code tags."""
        if not url.startswith(("http://", "https://")):
            return "[NETWORK ERROR] Security Volatility Check: Target URL protocol must be HTTP or HTTPS."
            
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) GM-AI-Core/1.0'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                raw_data = response.read()
                
                # Check if payload structure is JSON data
                try:
                    json_data = json.loads(raw_data.decode('utf-8'))
                    return f"[LIVE JSON PAYLOAD]\n{json.dumps(json_data, indent=2)}"
                except json.JSONDecodeError:
                    pass
                
                # Fallback to plain text processing, stripping out HTML tag boundaries
                html_text = raw_data.decode('utf-8', errors='ignore')
                clean_text = re.sub(r'<[^>]+>', '', html_text) 
                normalized_space = re.sub(r'\s+', ' ', clean_text).strip()
                return f"[LIVE WEB PAGE CONTENT]\n{normalized_space[:1500]}..." 
                
        except Exception as e:
            return f"[NETWORK PIPELINE FAILURE] Could not scrape target URL: {str(e)}"

