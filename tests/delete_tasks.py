import sys
import os
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.label_studio import LabelStudioClient

# Configure logging
logging.basicConfig(level=logging.INFO)

def delete_all_tasks():
    username = os.getenv("LABEL_STUDIO_USERNAME", "user@example.com")
    password = os.getenv("LABEL_STUDIO_PASSWORD", "password123")
    
    client = LabelStudioClient(username=username, password=password, url="http://localhost:8080")
    
    project_id = 7
    print(f"Deleting all tasks from Project {project_id}...")
    
    try:
        # Get all task IDs
        url = f"{client.url}/api/tasks?project={project_id}&page_size=10000"
        response = client.session.get(url)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, dict) and 'tasks' in data:
             tasks = data['tasks']
        elif isinstance(data, list):
            tasks = data
        else:
            tasks = []
            
        task_ids = [t['id'] for t in tasks]
        print(f"Found {len(task_ids)} tasks to delete.")
        
        if not task_ids:
            return

        # Delete tasks
        # API: POST /api/dm/actions?id=delete_tasks&project={id}
        # Body: { "ordering": [], "selectedItems": { "all": false, "included": [ids] }, "filters": { "conjunction": "and", "items": [] } }
        
        payload = {
            "ordering": [],
            "selectedItems": {
                "all": False,
                "included": task_ids
            },
            "filters": {
                "conjunction": "and",
                "items": []
            },
            "project": project_id
        }
        
        # Note: The endpoint might be /api/dm/actions or /api/tasks/delete
        # Let's try the bulk delete action which is standard in LS UI
        
        action_url = f"{client.url}/api/dm/actions?id=delete_tasks&project={project_id}"
        resp = client.session.post(action_url, json=payload)
        
        if resp.status_code != 200:
            # Try individual delete if bulk fails (older API?)
            print("Bulk delete failed, trying individual delete...")
            for tid in task_ids:
                client.session.delete(f"{client.url}/api/tasks/{tid}")
                print(f"Deleted task {tid}")
        else:
            print("Successfully deleted all tasks.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    delete_all_tasks()
