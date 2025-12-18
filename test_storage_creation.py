import os
import requests
from src.utils.label_studio import LabelStudioClient

# Set env vars
os.environ["LABEL_STUDIO_USERNAME"] = "user@example.com"
os.environ["LABEL_STUDIO_PASSWORD"] = "password123"
os.environ["LABEL_STUDIO_URL"] = "http://localhost:8080"

def test_storage():
    client = LabelStudioClient(
        username=os.environ["LABEL_STUDIO_USERNAME"],
        password=os.environ["LABEL_STUDIO_PASSWORD"]
    )
    
    print("Logging in...")
    client.login()
    
    # 1. Get or Create Project
    project_id = client.get_or_create_project("Debug Project", "<View></View>")
    print(f"Project ID: {project_id}")
    
    # 2. Create Local Storage
    storage_payload = {
        "path": "/label-studio/files",
        "use_blob_urls": True,
        "title": "Local Files",
        "project": project_id,
        "regex_filter": ".*",
        "description": "Automatically created storage"
    }
    
    print("Creating Local Storage...")
    try:
        resp = client.session.post(f"{client.url}/api/storages/localfiles", json=storage_payload)
        print(f"Storage Creation Status: {resp.status_code}")
        print(resp.text)
    except Exception as e:
        print(f"Failed to create storage: {e}")
        
    # 3. Test File Access
    # With DOCUMENT_ROOT=/, and d=label-studio/files/Nov20/...
    # The full path is /label-studio/files/Nov20/...
    # The storage path is /label-studio/files.
    # /label-studio/files is a prefix of /label-studio/files/Nov20/...
    # So it should match!
    
    video_path = "label-studio/files/Nov20/Group1_Saline-3/211673_Nov20_Saline-3.mp4"
    url = f"{client.url}/data/local-files/?d={video_path}"
    
    print(f"Testing URL: {url}")
    resp = client.session.get(url)
    print(f"Status Code: {resp.status_code}")

if __name__ == "__main__":
    test_storage()
