import sys
import os
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.label_studio import LabelStudioClient
from components.label_studio_config import LABEL_STUDIO_CONFIG, PROJECT_TITLE

# Configure logging
logging.basicConfig(level=logging.INFO)

def validate_config():
    # Use default credentials from docker-compose
    username = "user@example.com"
    password = "password123"
    
    # Allow override via env vars
    if os.getenv("LABEL_STUDIO_USERNAME"):
        username = os.getenv("LABEL_STUDIO_USERNAME")
    if os.getenv("LABEL_STUDIO_PASSWORD"):
        password = os.getenv("LABEL_STUDIO_PASSWORD")
    
    client = LabelStudioClient(username=username, password=password, url="http://localhost:8080")
    
    print(f"Connecting to Label Studio at {client.url}...")
    connected, msg = client.check_connection()
    
    if not connected:
        print(f"Failed to connect: {msg}")
        return
        
    print("Connected!")
    
    # Get project
    try:
        # This should trigger the update_project_config logic we just added
        project_id = client.get_or_create_project(PROJECT_TITLE, LABEL_STUDIO_CONFIG)
        print(f"Project ID: {project_id}")
        
        # Verify config
        response = client.session.get(f"{client.url}/api/projects/{project_id}")
        project_data = response.json()
        current_config = project_data.get('label_config')
        
        print("\nCurrent Config on Server:")
        print(current_config)
        
        print("\nExpected Config:")
        print(LABEL_STUDIO_CONFIG)
        
        # Normalize for comparison
        norm_current = "".join(current_config.split())
        norm_expected = "".join(LABEL_STUDIO_CONFIG.split())
        
        if norm_current == norm_expected:
            print("\n✅ Configuration matches!")
        else:
            print("\n❌ Configuration is different.")
            print(f"Server: {norm_current[:50]}...")
            print(f"Local:  {norm_expected[:50]}...")
                 
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    validate_config()
