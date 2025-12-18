import sys
import os
import logging
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.label_studio import LabelStudioClient

# Configure logging
logging.basicConfig(level=logging.INFO)

def list_projects():
    username = os.getenv("LABEL_STUDIO_USERNAME", "user@example.com")
    password = os.getenv("LABEL_STUDIO_PASSWORD", "password123")
    
    client = LabelStudioClient(username=username, password=password, url="http://localhost:8080")
    
    print("Listing projects...")
    try:
        response = client.session.get(f"{client.url}/api/projects")
        response.raise_for_status()
        data = response.json()
        
        projects = data.get('results', [])
        print(f"Found {len(projects)} projects.")
        
        for p in projects:
            print(f"ID: {p['id']}, Title: {p['title']}, Created: {p['created_at']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_projects()
