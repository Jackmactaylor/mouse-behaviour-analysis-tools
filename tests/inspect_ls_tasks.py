import sys
import os
import logging
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.label_studio import LabelStudioClient

# Configure logging
logging.basicConfig(level=logging.INFO)

def inspect_tasks():
    # Use default credentials
    username = os.getenv("LABEL_STUDIO_USERNAME", "user@example.com")
    password = os.getenv("LABEL_STUDIO_PASSWORD", "password123")
    
    client = LabelStudioClient(username=username, password=password, url="http://localhost:8080")
    
    print("Checking connection...")
    connected, msg = client.check_connection()
    print(f"Connection status: {connected}, {msg}")
    
    if not connected:
        return
    
    # Find project by title
    project_id = None
    try:
        p_resp = client.session.get(f"{client.url}/api/projects")
        p_resp.raise_for_status()
        projects = p_resp.json().get('results', [])
        for p in projects:
            if p['title'] == "Mouse Behavior Analysis":
                project_id = p['id']
                break
    except Exception as e:
        print(f"Error listing projects: {e}")
        return

    if not project_id:
        print("Project 'Mouse Behavior Analysis' not found.")
        return
    
    print(f"Inspecting tasks for Project {project_id}...")
    
    try:
        # Check project details first
        p_url = f"{client.url}/api/projects/{project_id}"
        print(f"Fetching project details from {p_url}...")
        p_resp = client.session.get(p_url, timeout=5)
        p_resp.raise_for_status()
        project = p_resp.json()
        print(f"Project Title: {project.get('title')}")
        print(f"Task Count: {project.get('task_number')}")
        
        # Get tasks using the correct endpoint
        url = f"{client.url}/api/tasks?project={project_id}&page_size=10"
        print(f"Fetching tasks from {url}...")
        response = client.session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"Response type: {type(data)}")
        if isinstance(data, dict):
            print(f"Keys: {data.keys()}")
            
        # The response might be paginated { "count": ..., "results": [...] } or a list
        if isinstance(data, dict) and 'results' in data:
            tasks = data['results']
        elif isinstance(data, dict) and 'tasks' in data:
             tasks = data['tasks']
        elif isinstance(data, list):
            tasks = data
        else:
            print("Unknown response format")
            tasks = []
            
        print(f"Found {len(tasks)} tasks.")
        
        if len(tasks) > 0:
            print("\nSample Task Data:")
            for i, task in enumerate(tasks):
                if i >= 1: break
                print(f"Task Index {i}: ID={task.get('id')}")
                print(f"Annotations: {json.dumps(task.get('annotations'), indent=2)}")
                print(f"Predictions: {json.dumps(task.get('predictions'), indent=2)}")
                
            # Check for duplicate IDs
            ids = [t.get('id') for t in tasks]
            if len(ids) != len(set(ids)):
                print("\n⚠️ WARNING: Duplicate Task IDs found!")
            else:
                print("\nTask IDs look unique.")
                
            if all(t.get('id') == 0 for t in tasks):
                print("\n❌ CRITICAL: All Task IDs are 0. This confirms the issue.")
        else:
            print("No tasks found.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_tasks()
