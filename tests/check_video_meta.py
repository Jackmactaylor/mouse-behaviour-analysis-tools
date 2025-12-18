import subprocess
import os
import json

def get_video_info(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    cmd = [
        "ffprobe", 
        "-v", "error", 
        "-select_streams", "v:0", 
        "-show_entries", "stream=width,height,duration,r_frame_rate,nb_frames", 
        "-of", "json", 
        file_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return
            
        info = json.loads(result.stdout)
        print(f"File: {file_path}")
        print(json.dumps(info, indent=2))
        
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    # Check one of the processed files found in the task list
    # Path from task: /workspace/processed/Nov20/Group1_Saline-3/211673_Nov20_Saline-3.mp4
    # But on host (Windows), it is mapped to workspace/processed/...
    
    # I need to find where the workspace is on the host.
    # The workspace_info says: c:\Users\tomtaylor\Documents\GitHub\mouse-behaviour-analysis-tools
    # So workspace is at ./workspace
    
    base_dir = r"c:\Users\tomtaylor\Documents\GitHub\mouse-behaviour-analysis-tools\workspace\processed"
    
    # Recursive search
    found = False
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".mp4"):
                full_path = os.path.join(root, file)
                get_video_info(full_path)
                found = True
                break 
        if found: break
        
    if not found:
        print("No MP4 files found in processed directory.")
