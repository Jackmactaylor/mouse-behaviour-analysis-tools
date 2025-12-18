import requests
import os

# Configuration from docker-compose.yml
USERNAME = "user@example.com"
PASSWORD = "password123"
BASE_URL = "http://localhost:8080"

def test_session_login():
    print("Testing Session Login...")
    session = requests.Session()
    
    # 1. Get Login Page to get CSRF token
    login_url = f"{BASE_URL}/user/login/"
    try:
        print(f"GET {login_url}")
        resp = session.get(login_url)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print("Failed to load login page")
            return

        csrftoken = session.cookies.get('csrftoken')
        print(f"CSRF Token: {csrftoken}")
        
        if not csrftoken:
            print("No CSRF token found")
            return

        # 2. POST Login
        payload = {
            "email": USERNAME,
            "password": PASSWORD,
            "csrfmiddlewaretoken": csrftoken
        }
        
        print(f"POST {login_url}")
        resp = session.post(login_url, data=payload, headers={"Referer": login_url})
        print(f"Status: {resp.status_code}")
        
        # Check if we were redirected (usually means success)
        print(f"URL after login: {resp.url}")
        
        # 3. Test API Access
        api_url = f"{BASE_URL}/api/projects"
        print(f"GET {api_url}")
        resp = session.get(api_url)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("Success! Session authentication works.")
            print(f"Projects: {resp.json()}")
        else:
            print(f"Failed to access API. Response: {resp.text[:200]}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_session_login()
