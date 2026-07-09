import urllib.request
import json

def test_ollama_stream(model_name="gpt-oss:120b-cloud"):
    # We use explicit host formatting to bypass Windows getaddrinfo restrictions
    host = "127.0.0.1"
    port = 11434
    url = f"http://{host}:{port}/api/generate"
    
    payload = {
        "model": model_name,
        "prompt": "Integrate GM AI Bot-Sitter pipeline initialized. Confirm system status.",
        "stream": True
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url, 
        data=data, 
        headers={
            'Content-Type': 'application/json',
            'Host': f'{host}:{port}'
        }
    )
    
    print(f"Connecting to live Ollama pipeline using model: {model_name}...")
    try:
        with urllib.request.urlopen(req) as response:
            print("\n--- Live Stream Output ---")
            for line in response:
                if line:
                    try:
                        line_data = json.loads(line.decode('utf-8').strip())
                        print(line_data.get("response", ""), end="", flush=True)
                    except json.JSONDecodeError:
                        pass
            print("\n--------------------------\nPipeline test successful.")
            
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")

if __name__ == "__main__":
    test_ollama_stream()

