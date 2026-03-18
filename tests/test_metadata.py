import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.metadata import parse_video_path, parse_video_filename, load_group_map

def test_parse_video_filename():
    """Test the filename parser with known format: {treatment}_{date}-{index}.ext"""
    meta = parse_video_filename("Saline-3_Nov20-1.mp4")
    assert meta["treatment"] == "Saline-3", f"Expected 'Saline-3', got {meta['treatment']}"
    assert meta["date"] == "Nov20", f"Expected 'Nov20', got {meta['date']}"

    # Filename without index
    meta2 = parse_video_filename("DrugA_Jan15.mp4")
    assert meta2["treatment"] == "DrugA", f"Expected 'DrugA', got {meta2['treatment']}"
    assert meta2["date"] == "Jan15", f"Expected 'Jan15', got {meta2['date']}"

    # Filename with no underscore (fallback regex for date)
    meta3 = parse_video_filename("Video.mp4")
    assert meta3["treatment"] == "Unknown"
    assert meta3["date"] == "Unknown"

def test_load_group_map_defaults():
    """When no CSV exists, load_group_map should return sensible defaults."""
    defaults = load_group_map("/nonexistent/path.csv")
    assert "Group 1" in defaults
    assert "Group 2" in defaults
    assert "treatment" in defaults["Group 1"]
    assert "cages" in defaults["Group 1"]

def test_parse_video_path_unknown_group():
    """A path that matches no group in the default map should return group=Unknown."""
    meta = parse_video_path("/workspace/raw/RandomFolder/Video.mp4")
    assert meta["group"] == "Unknown", f"Expected 'Unknown', got {meta['group']}"

if __name__ == "__main__":
    test_parse_video_filename()
    test_load_group_map_defaults()
    test_parse_video_path_unknown_group()
    print("\nAll tests passed!")
