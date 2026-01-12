import requests
import logging
import os
import sqlite3
import uuid
import urllib.parse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_local_api_key(db_path='/label-studio-data/label_studio.sqlite3'):
    """
    Retrieve the API key directly from the Label Studio SQLite database.
    This is useful when running in the same Docker stack.
    """
    if not os.path.exists(db_path):
        logger.warning(f"Label Studio DB not found at {db_path}")
        return None
    
    try:
        # Open in read-only mode if possible, but sqlite3.connect doesn't strictly enforce it like 'file:...?mode=ro' without uri=True
        # We rely on the docker mount being ro
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        # Get the first token found. In a single-user setup, this is usually correct.
        cursor.execute("SELECT key FROM authtoken_token ORDER BY created DESC LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
    except Exception as e:
        logger.error(f"Failed to retrieve API key from DB: {e}")
        
    return None

class LabelStudioClient:
    def __init__(self, api_key=None, url=None, username=None, password=None):
        """
        Initialize the Label Studio Client.
        
        Args:
            api_key (str, optional): The API token for authentication.
            url (str, optional): The base URL of the Label Studio instance. 
                                 Defaults to 'http://label-studio:8080' (Docker service name).
            username (str, optional): Username for login-based auth.
            password (str, optional): Password for login-based auth.
        """
        self.api_key = api_key
        self.username = username
        self.password = password
        self.session = requests.Session()
        
        # Default to Docker service name if not provided, or localhost if running locally
        if not url:
            self.url = os.getenv("LABEL_STUDIO_URL", "http://label-studio:8080")
        else:
            self.url = url.rstrip('/')
            
        if self.api_key:
            self.headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "application/json"
            }
            self.session.headers.update(self.headers)
        elif self.username and self.password:
            self.login()
        else:
            logger.warning("No API key or credentials provided. Client may not be authenticated.")

    def login(self):
        """Log in to Label Studio using username/password to get a session."""
        try:
            login_url = f"{self.url}/user/login/"
            # Get CSRF token
            resp = self.session.get(login_url)
            resp.raise_for_status()
            csrftoken = self.session.cookies.get('csrftoken')
            
            if not csrftoken:
                raise ValueError("Could not retrieve CSRF token")
                
            payload = {
                "email": self.username,
                "password": self.password,
                "csrfmiddlewaretoken": csrftoken
            }
            
            # Perform login
            resp = self.session.post(login_url, data=payload, headers={"Referer": login_url})
            resp.raise_for_status()
            
            # Verify auth by checking if we are redirected or can access API
            if resp.url == login_url:
                 raise ValueError("Login failed (redirected back to login page)")
                 
            logger.info(f"Successfully logged in as {self.username}")
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise

    def check_connection(self):
        """
        Verify connection to Label Studio API.
        
        Returns:
            tuple: (bool, str) - (Success, Error Message)
        """
        try:
            # The /api/projects endpoint is a good health check that requires auth
            response = self.session.get(f"{self.url}/api/projects", timeout=5)
            response.raise_for_status()
            return True, "Connected"
        except requests.exceptions.RequestException as e:
            error_msg = f"Connection failed: {e}"
            logger.error(error_msg)
            return False, error_msg

    def get_or_create_project(self, title, label_config):
        """
        Get an existing project by title or create a new one.
        If the project exists, update its label configuration to ensure it matches the latest version.
        
        Args:
            title (str): The title of the project.
            label_config (str): The XML configuration for the labeling interface.
            
        Returns:
            int: The project ID.
        """
        # 1. List projects to see if it exists
        try:
            response = self.session.get(f"{self.url}/api/projects")
            response.raise_for_status()
            projects = response.json().get('results', [])
            
            for p in projects:
                if p['title'] == title:
                    logger.info(f"Found existing project '{title}' (ID: {p['id']})")
                    # Update the config to ensure it's current
                    self.update_project_config(p['id'], label_config)
                    return p['id']
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list projects: {e}")
            raise

        # 2. Create new project if not found
        payload = {
            "title": title,
            "label_config": label_config,
            "expert_instruction": "Please label the video segments.",
            "show_instruction": False,
            "show_skip_button": True,
            "enable_empty_annotation": True,
            "color": "#FF0000"
        }
        
        try:
            # Use session for request, headers are handled by session or not needed if cookie auth
            response = self.session.post(f"{self.url}/api/projects", json=payload)
            response.raise_for_status()
            project = response.json()
            logger.info(f"Created new project '{title}' (ID: {project['id']})")
            return project['id']
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create project: {e}")
            raise

    def update_project_config(self, project_id, label_config):
        """
        Update the label configuration for an existing project.
        
        Args:
            project_id (int): The ID of the project.
            label_config (str): The new XML configuration.
        """
        try:
            url = f"{self.url}/api/projects/{project_id}"
            payload = {"label_config": label_config}
            response = self.session.patch(url, json=payload)
            response.raise_for_status()
            logger.info(f"Updated configuration for Project {project_id}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update project config: {e}")
            # Don't raise here, as we might still want to proceed with the old config if update fails
            # But usually this is critical. Let's log it.

    def import_tasks(self, project_id, tasks):
        """
        Import tasks into a specific project.
        
        Args:
            project_id (int): The ID of the project.
            tasks (list): A list of task dictionaries. 
                          Example: [{"video": "/data/local-files/?d=video.mp4", "meta": {...}}]
                          
        Returns:
            dict: The response from the import API.
        """
        try:
            url = f"{self.url}/api/projects/{project_id}/import"
            response = self.session.post(url, json=tasks)
            response.raise_for_status()
            logger.info(f"Successfully imported {len(tasks)} tasks to Project {project_id}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to import tasks: {e}")
            raise

    @staticmethod
    def format_prediction_result(segments, model_version="Heuristic_v1", duration=None):
        """
        Formats a list of time segments into a Label Studio prediction payload.
        
        Args:
            segments (list): List of dicts {'start': float, 'end': float, 'label': str}
            model_version (str): Identifier for the model.
            duration (float, optional): Total duration of the audio/video in seconds.
            
        Returns:
            dict: A prediction object ready to be added to a task's 'predictions' list.
        """
        results = []
        for seg in segments:
            # Generate a unique ID for the region
            region_id = str(uuid.uuid4())[:8] # Short UUID is usually sufficient and cleaner
            
            result_item = {
                "id": region_id,
                "value": {
                    "start": seg['start'],
                    "end": seg['end'],
                    # "channel": 0, # Removed channel to avoid issues with mono/stereo mismatch
                    "labels": [seg['label']]
                },
                # These names must match the XML config
                "from_name": "label",
                "to_name": "audio", 
                "type": "labels"
            }
            
            if duration:
                result_item["original_length"] = duration
                
            results.append(result_item)
            
        return {
            "model_version": model_version,
            "result": results
        }

    def create_local_storage(self, project_id, path, title="Local Files"):
        """
        Create a Local Storage connection for the project.
        
        Args:
            project_id (int): The ID of the project.
            path (str): The absolute path to the directory on the server.
            title (str): The title of the storage.
        """
        # Check if storage already exists
        try:
            response = self.session.get(f"{self.url}/api/storages/localfiles?project={project_id}")
            response.raise_for_status()
            storages = response.json()
            for s in storages:
                if s['path'] == path:
                    logger.info(f"Local storage for path '{path}' already exists (ID: {s['id']})")
                    return s['id']
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to list storages: {e}")

        # Create new storage
        payload = {
            "path": path,
            "use_blob_urls": True,
            "title": title,
            "project": project_id,
            "regex_filter": ".*",
            "description": "Automatically created storage"
        }
        
        try:
            response = self.session.post(f"{self.url}/api/storages/localfiles", json=payload)
            response.raise_for_status()
            storage = response.json()
            logger.info(f"Created local storage '{title}' (ID: {storage['id']})")
            return storage['id']
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create local storage: {e}")
            raise

    def create_task(self, project_id, task_data):
        """
        Create a single task and return its ID.
        
        Args:
            project_id (int): The ID of the project.
            task_data (dict): The task data (e.g. {"video": "...", "meta": ...})
            
        Returns:
            int: The ID of the created task, or None if failed.
        """
        # Import the task
        self.import_tasks(project_id, [task_data])
        
        # Fetch the ID by filtering on the video URL
        # This assumes 'video' is a key in the task_data or task_data['data']
        video_url = task_data.get('data', {}).get('video') or task_data.get('video')
        
        if not video_url:
            logger.warning("Could not determine video URL to fetch task ID.")
            return None
            
        try:
            # Fetch tasks and filter client-side because server-side filtering/ordering is unreliable
            # We fetch a large page size to ensure we find the new task
            url = f"{self.url}/api/tasks?project={project_id}&page_size=100"
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Handle pagination/list response
            if isinstance(data, dict) and 'tasks' in data:
                 tasks = data['tasks']
            elif isinstance(data, list):
                 tasks = data
            else:
                 tasks = []
            
            # Filter by video URL and find the latest ID
            matching_tasks = []
            for t in tasks:
                t_video = t.get('data', {}).get('video')
                # Compare strings directly
                if t_video == video_url:
                    matching_tasks.append(t)
            
            if matching_tasks:
                # Sort by ID descending to get the latest one
                matching_tasks.sort(key=lambda x: x['id'], reverse=True)
                return matching_tasks[0]['id']
            else:
                logger.warning(f"Task created but not found via list: {video_url}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch task ID: {e}")
            return None

    def create_annotation(self, task_id, annotation_payload):
        """
        Create an annotation for a specific task.
        
        Args:
            task_id (int): The ID of the task.
            annotation_payload (dict): The annotation object.
            
        Returns:
            dict: The created annotation.
        """
        try:
            url = f"{self.url}/api/tasks/{task_id}/annotations"
            response = self.session.post(url, json=annotation_payload)
            response.raise_for_status()
            logger.info(f"Created annotation for Task {task_id}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create annotation: {e}")
            raise
