import sys
import os
import logging
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.label_studio import LabelStudioClient

# Configure logging
logging.basicConfig(level=logging.INFO)

def inspect_project_8():
    username = os.getenv("LABEL_STUDIO_USERNAME", "user@example.com")
    password = os.getenv("LABEL_STUDIO_PASSWORD", "password123")
    
    client = LabelStudioClient(username=username, password=password, url="http://localhost:8080")
    
    project_id = 8
    print(f"Inspecting Project {project_id}...")
    
    try:
        # Get project config
        p_url = f"{client.url}/api/projects/{project_id}"
        p_resp = client.session.get(p_url)
        project = p_resp.json()
        print("\nCurrent Config:")
        print(project.get('label_config'))
        
        # Get first task
        url = f"{client.url}/api/tasks?project={project_id}&page_size=1"
        response = client.session.get(url)
        data = response.json()
        
        if isinstance(data, dict) and 'tasks' in data:
             tasks = data['tasks']
        elif isinstance(data, list):
            tasks = data
        else:
            tasks = []
            
        if tasks:
            print("\nFirst Task Data:")
            print(json.dumps(tasks[0].get('data'), indent=2))
        else:
            print("\nNo tasks found.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_project_8()
