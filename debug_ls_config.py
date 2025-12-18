import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from utils.label_studio import LabelStudioClient

# Set env vars for localhost access
os.environ['LABEL_STUDIO_URL'] = 'http://localhost:8080'
# Default credentials from guide
os.environ['LABEL_STUDIO_USERNAME'] = 'user@example.com'
os.environ['LABEL_STUDIO_PASSWORD'] = 'password123'

def check_config():
    client = LabelStudioClient(
        username=os.environ['LABEL_STUDIO_USERNAME'],
        password=os.environ['LABEL_STUDIO_PASSWORD']
    )
    
    try:
        client.check_connection()
        print("Connected to Label Studio")
        
        # Get project
        response = client.session.get(f"{client.url}/api/projects")
        response.raise_for_status()
        projects = response.json().get('results', [])
        
        target_project = None
        for p in projects:
            if p['title'] == "Mouse Behavior Analysis":
                target_project = p
                break
        
        if target_project:
            print(f"Found Project ID: {target_project['id']}")
            print("Current XML Config:")
            print(target_project['label_config'])
        else:
            print("Project 'Mouse Behavior Analysis' not found.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_config()
