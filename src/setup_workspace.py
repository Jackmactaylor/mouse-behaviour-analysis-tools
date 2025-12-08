import os
import pathlib

def setup_workspace():
    """
    Creates the standard directory structure for the project.
    """
    # Define the root workspace directory relative to this script
    # Assuming script is in src/, workspace is in root/workspace
    project_root = pathlib.Path(__file__).parent.parent
    workspace_root = project_root / "workspace"
    
    subdirs = ["raw", "processed", "outputs"]
    
    print(f"Setting up workspace at: {workspace_root}")
    
    if not workspace_root.exists():
        workspace_root.mkdir()
        print(f"Created {workspace_root}")
        
    for subdir in subdirs:
        path = workspace_root / subdir
        if not path.exists():
            path.mkdir()
            print(f"Created {path}")
        else:
            print(f"Exists {path}")

    # Create .gitignore in workspace to ignore all content except .gitkeep if we wanted, 
    # but the root .gitignore should handle it. 
    # Let's just ensure the root .gitignore exists and has the entry.
    gitignore_path = project_root / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            content = f.read()
        
        if "workspace/" not in content:
            print("Adding workspace/ to .gitignore")
            with open(gitignore_path, "a") as f:
                f.write("\n# Ignore workspace data\nworkspace/\n!workspace/.gitkeep\n")
    else:
        print("Creating .gitignore")
        with open(gitignore_path, "w") as f:
            f.write("# Ignore workspace data\nworkspace/\n!workspace/.gitkeep\n")

if __name__ == "__main__":
    setup_workspace()
