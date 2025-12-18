import requests
import os
import sqlite3

# Configuration from docker-compose.yml
USERNAME = "user@example.com"
PASSWORD = "password123"
BASE_URL = "http://localhost:8080"

def get_db_token():
    db_path = 'label-studio_data/label_studio.sqlite3'
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}")
        return None
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute("SELECT key FROM authtoken_token ORDER BY created DESC LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
    except Exception as e:
        print(f"DB Error: {e}")
    return None

def test_legacy_token(token):
    print(f"\nTesting Legacy Token: {token}")
    headers = {"Authorization": f"Token {token}"}
    try:
        resp = requests.get(f"{BASE_URL}/api/projects", headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

def test_login_endpoint():
    print("\nTesting Login Endpoints...")
    # Try to find the correct endpoint and payload
    url = f"{BASE_URL}/api/users/token"
    
    payloads = [
        {"email": USERNAME, "password": PASSWORD},
        {"username": USERNAME, "password": PASSWORD}
    ]

    for p in payloads:
        print(f"Trying {url} with keys {list(p.keys())}...")
        try:
            resp = requests.post(url, json=p)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                print(f"Success! Response: {resp.json()}")
                return
            else:
                 print(f"Response: {resp.text[:200]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    token = get_db_token()
    if token:
        test_legacy_token(token)
    else:
        print("No token found in DB")
        
    test_login_endpoint()
