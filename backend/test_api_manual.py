import requests
import json

BASE_URL = "http://localhost:8000"

def test_root():
    try:
        r = requests.get(f"{BASE_URL}/")
        print(f"Root: {r.status_code}")
        print(r.json())
    except Exception as e:
        print(f"Server not running? {e}")

def test_generate_plan():
    payload = {
        "start_date": "2023-10-23",
        "end_date": "2023-10-29",
        "content": {}, # Ignored by logic, determined by backend
        "feedback": "I feel great, want to run a long run on Sunday."
    }
    # Note: This will fail if no user in DB or no API key, but verifies endpoint existence
    try:
        r = requests.post(f"{BASE_URL}/coach/generate", json=payload)
        print(f"Generate: {r.status_code}")
        if r.status_code == 200:
            print(json.dumps(r.json(), indent=2))
        else:
            print(r.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Testing API...")
    test_root()
    # test_generate_plan() # Uncomment to test if server running with env vars
