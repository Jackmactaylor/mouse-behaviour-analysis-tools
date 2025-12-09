import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.metadata import parse_video_path, GROUP_MAP

def test_metadata_parsing():
    # Test Case 1: Standard Path
    path1 = "/workspace/raw/Group 1: Saline-3/Saline-3_Dec2.M4V"
    meta1 = parse_video_path(path1)
    print(f"Path: {path1}")
    print(f"Result: {meta1}")
    assert meta1["group"] == "Group 1"
    assert meta1["treatment"] == "Saline"
    assert meta1["date"] == "Dec2"
    
    # Test Case 2: Windows Path (simulated)
    path2 = "workspace\\raw\\Group 2 - DrugA\\Video_Jan15.mp4"
    meta2 = parse_video_path(path2, root_dir="workspace\\raw")
    print(f"\nPath: {path2}")
    print(f"Result: {meta2}")
    assert meta2["group"] == "Group 2"
    assert meta2["treatment"] == "DrugA"
    assert meta2["date"] == "Jan15"

    # Test Case 3: Unknown Group
    path3 = "/workspace/raw/RandomFolder/Video.mp4"
    meta3 = parse_video_path(path3)
    print(f"\nPath: {path3}")
    print(f"Result: {meta3}")
    assert meta3["group"] == "Unknown"

if __name__ == "__main__":
    test_metadata_parsing()
    print("\nAll tests passed!")
