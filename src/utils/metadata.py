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
    Parses the filename to extract date, treatment, or other info if present.
    Expected format: {treatment}_{date}-{index}.ext
    Example: Saline-3_Nov20-1.mp4 
             -> Treatment: Saline-3
             -> Date: Nov20
    """
    path = Path(filename)
    stem = path.stem # Remove extension
    
    metadata = {
        "date": "Unknown",
        "treatment": "Unknown"
    }
    
    # Attempt to split by last underscore
    # Saline-3_Nov20-1 -> ['Saline-3', 'Nov20-1']
    if '_' in stem:
        try:
            treatment_part, date_part = stem.rsplit('_', 1)
            
            # Extract date from date-index part (Nov20-1 -> Nov20)
            if '-' in date_part:
                date_val = date_part.split('-')[0]
            else:
                date_val = date_part # Fallback if no index
            
            metadata["treatment"] = treatment_part
            metadata["date"] = date_val
            return metadata
        except ValueError:
            pass
            
    # Fallback to old regex for date if format doesn't match
    date_match = re.search(r"([A-Z][a-z]{2}\d{1,2})", filename)
    if date_match:
        metadata["date"] = date_match.group(1)
        
    return metadata

def parse_video_path(file_path: str, root_dir: str = "/workspace/raw") -> Dict:
    """
    Parses the full file path to extract metadata.
    Prioritizes flat filename convention: {treatment}_{date}-{index}
    Falls back to folder structure: .../{Group Folder}/{Filename}
    
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

    # 1. Parse Filename for Date and Treatment
    file_meta = parse_video_filename(path.name)
    metadata.update(file_meta)

    # Load the map dynamically
    group_map = load_group_map()

    # 2. Try to match Treatment from filename to Group Map (New Flat Structure)
    if metadata["treatment"] != "Unknown":
        for g_name, g_data in group_map.items():
            if g_data.get("treatment", "").strip() == metadata["treatment"].strip():
                metadata["group"] = g_name
                metadata["mouse_ids"] = g_data.get("cages", ["Unknown"]*4)
                # Ensure the mapped treatment is used (cleaner)
                metadata["treatment"] = g_data.get("treatment") 
                return metadata

    # 3. Fallback: Parse Folder Structure for Group/Treatment (Old Nested Structure)
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
