import os
import re
import csv
from pathlib import Path
from typing import Dict, List, Optional

# Path to the CSV map
MOUSE_MAP_PATH = "/workspace/mouse_map.csv"

def load_group_map(csv_path: str = MOUSE_MAP_PATH) -> Dict:
    """Loads the Group -> MouseID mapping from a CSV file."""
    group_map = {}
    
    # Fallback defaults if file doesn't exist
    defaults = {
        "Group 1": {"treatment": "example A", "cages": ["123", "124", "125", "126"]},
        "Group 2": {"treatment": "example B", "cages": ["127", "128", "129", "130"]},
    }

    if not os.path.exists(csv_path):
        return defaults
    
    try:
        with open(csv_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Expected columns: Group, Treatment, Cage1, Cage2, Cage3, Cage4
                group = row.get("Group", "").strip()
                if group:
                    group_map[group] = {
                        "treatment": row.get("Treatment", "Unknown"),
                        "cages": [
                            row.get("Cage1", "Unknown"),
                            row.get("Cage2", "Unknown"),
                            row.get("Cage3", "Unknown"),
                            row.get("Cage4", "Unknown")
                        ]
                    }
    except Exception as e:
        print(f"Error loading mouse map: {e}")
        return defaults
        
    return group_map if group_map else defaults

def parse_video_filename(filename: str) -> Dict[str, str]:
    """
    Parses the filename to extract date or other info if present.
    Example: Saline-3_Dec2.M4V -> Date: Dec2
    """
    # Simple regex to find date-like patterns e.g. Dec2, Jan15
    date_match = re.search(r"([A-Z][a-z]{2}\d{1,2})", filename)
    date = date_match.group(1) if date_match else "UnknownDate"
    return {"date": date}

def parse_video_path(file_path: str, root_dir: str = "/workspace/raw") -> Dict:
    """
    Parses the full file path to extract metadata based on folder structure.
    Expected structure: .../{Group Folder}/{Filename}
    
    Returns:
        dict: {
            "mouse_ids": [id1, id2, id3, id4],
            "treatment": str,
            "date": str,
            "group": str
        }
    """
    path = Path(file_path)
    try:
        # If the path is absolute and starts with root_dir, get relative path
        if path.is_absolute() and str(path).startswith(root_dir):
            relative_path = path.relative_to(root_dir)
        else:
            relative_path = path
    except ValueError:
        relative_path = path

    parts = relative_path.parts
    
    metadata = {
        "mouse_ids": ["Unknown", "Unknown", "Unknown", "Unknown"],
        "treatment": "Unknown",
        "date": "Unknown",
        "group": "Unknown"
    }

    # 1. Parse Filename for Date
    file_meta = parse_video_filename(path.name)
    metadata.update(file_meta)

    # 2. Parse Folder Structure for Group/Treatment
    # Load the map dynamically
    group_map = load_group_map()
    
    # Look for group name in parent folders (iterating backwards from parent)
    # Example part: "Group 1: Saline-3"
    for part in reversed(parts[:-1]): 
        for group_key, group_data in group_map.items():
            if group_key in part:
                metadata["group"] = group_key
                metadata["treatment"] = group_data.get("treatment", "Unknown")
                metadata["mouse_ids"] = group_data.get("cages", ["Unknown"]*4)
                return metadata # Stop after finding the first match
    
    return metadata
