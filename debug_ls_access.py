import os
import sys
import requests
from src.utils.label_studio import LabelStudioClient

# Set env vars if not present
os.environ["LABEL_STUDIO_USERNAME"] = "user@example.com"
os.environ["LABEL_STUDIO_PASSWORD"] = "password123"
os.environ["LABEL_STUDIO_URL"] = "http://localhost:8080"

def test_video_access():
    print("Initializing client...")
    client = LabelStudioClient(
        username=os.environ["LABEL_STUDIO_USERNAME"],
        password=os.environ["LABEL_STUDIO_PASSWORD"]
    )
    
    print("Logging in...")
    try:
        client.login()
        print("Login successful.")
    except Exception as e:
        print(f"Login failed: {e}")
        return

    # Test multiple paths
    paths_to_test = [
        "/label-studio/files/Nov20/Group1_Saline-3/211673_Nov20_Saline-3.mp4",
        "Nov20/Group1_Saline-3/211673_Nov20_Saline-3.mp4",
        "/label-studio/files/test_from_container.txt",
        "test_from_container.txt"
    ]
    
    for p in paths_to_test:
        url = f"{client.url}/data/local-files/?d={p}"
        print(f"Testing URL: {url}")
        try:
            resp = client.session.get(url)
            print(f"Status Code: {resp.status_code}")
            if resp.status_code == 200:
                print(f"SUCCESS! Found at: {p}")
        except Exception as e:
            print(f"Error: {e}")
        print("-" * 20)

    # Test endpoint root
    url = f"{client.url}/data/local-files/"
    print(f"Testing Endpoint Root: {url}")
    try:
        resp = client.session.get(url)
        print(f"Status Code: {resp.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_video_access()
