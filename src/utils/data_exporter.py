import pandas as pd
import json
import os
import logging
from datetime import datetime
from utils.metadata import load_group_map

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_export_to_csv(export_data, output_path):
    """
    Process the Label Studio JSON export and save as CSV.
    
    Args:
        export_data (list): The JSON data returned from Label Studio export.
        output_path (str): The path to save the CSV file.
    
    Returns:
        str: Path to the saved CSV file, or None if failed.
    """
    records = []
    
    # Pre-compute MouseID -> Group lookup
    try:
        group_map = load_group_map()
        mouse_to_group_lookup = {}
        for g_name, g_info in group_map.items():
            for m_id in g_info.get('cages', []):
                if m_id and str(m_id).lower() != 'unknown':
                    mouse_to_group_lookup[str(m_id)] = g_name
    except Exception as e:
        logger.warning(f"Could not load group map for fallback lookup: {e}")
        mouse_to_group_lookup = {}
    
    for i, task in enumerate(export_data):
        # Get metadata from task data
        task_data = task.get('data', {})
        video_path = task_data.get('video', '')

        # DEBUG: Log the first task's structure to help diagnose missing fields
        if i == 0:
            logger.info(f"DEBUG - First Task Data Keys: {list(task_data.keys())}")
            logger.info(f"DEBUG - First Task Meta: {task_data.get('meta')}")
        
        # Try to get metadata from 'meta' field if it exists, otherwise parse filename?
        # Assuming the pipeline puts metadata in the 'meta' field during import.
        # But if not, we can parse the video path or filename.
        # Plan says: MouseID, Date, Treatment are important.
        
        # If meta is not explicitly in 'data', check if the user put it directly in 'data' properties
        # during import.
        # Let's fallback to parsing filename if needed, but prefer explicit meta.
        
        # NOTE: In Label Studio import, if we send {"data": {"video": "...", "mouse_id": "..."}}, 
        # it appears in data.
        
        meta = task_data.get('meta', {})
        
        mouse_id = task_data.get('mouse_id', meta.get('mouse_id', 'Unknown'))
        date_str = task_data.get('date', meta.get('date', 'Unknown'))
        treatment = task_data.get('treatment', meta.get('treatment', 'Unknown'))
        group = task_data.get('group', meta.get('group', 'Unknown'))
        
        # If 'Unknown', try to parse from filename as a fallback
        if mouse_id == 'Unknown' and video_path:
            filename = os.path.basename(video_path)
            # Expected: MouseID_Date_Treatment_Condition.mp4
            # e.g., 212753_Dec2_Control.mp4 (from file list in context)
            parts = filename.rsplit('.', 1)[0].split('_')
            if len(parts) >= 2:
                mouse_id = parts[0]
                date_str = parts[1]
            if len(parts) >= 3:
                treatment = parts[2]

        # Final Fallback: Look up Group from Mouse ID provided
        if group == 'Unknown' and mouse_id != 'Unknown':
            group = mouse_to_group_lookup.get(str(mouse_id), 'Unknown')
            
        # Check for multi-mouse IDs (List of 4 IDs)
        mouse_ids_list = task_data.get('mouse_ids', meta.get('mouse_ids', []))

        for annotation in task.get('annotations', []):
            # We only care about the final ground truth, usually the most recent one or 
            # simply all attached predictions/annotations. 
            # Phase 5 says "Re-upload Logic" and "Export Formatting".
            # Usually annotations are the human labels.
            
            for result in annotation.get('result', []):
                # We interpret "labels" type results
                if result.get('type') == 'labels':
                    value = result.get('value', {})
                    labels = value.get('labels', [])
                    start = value.get('start', 0)
                    end = value.get('end', 0)
                    duration = end - start
                    
                    # Assume one label per segment for now, or create multiple records
                    for label in labels:
                        # Determine Mouse ID for this specific label
                        current_mouse_id = mouse_id # Default to task-level ID
                        clean_behavior = label

                        # Logic for Multi-Mouse Labels: e.g. "Rubbing (M1)"
                        import re
                        # Look for (M1), (M2), etc.
                        match = re.search(r"\(M(\d+)\)", label)
                        if match and mouse_ids_list:
                            try:
                                # M1 -> index 0
                                idx = int(match.group(1)) - 1
                                if 0 <= idx < len(mouse_ids_list):
                                    current_mouse_id = mouse_ids_list[idx]
                                    # Strip the (Mx) suffix for clean reporting
                                    clean_behavior = re.sub(r"\s*\(M\d+\)", "", label).strip()
                            except (ValueError, IndexError):
                                pass

                        records.append({
                            'MouseID': current_mouse_id,
                            'Group': group,
                            'Date': date_str,
                            'Treatment': treatment,
                            'Behavior': clean_behavior,
                            'Rub_Start_Time': start,
                            'Rub_End_Time': end,
                            'Duration_Seconds': duration,
                            'Video_File': os.path.basename(video_path),
                            'Annotator_ID': annotation.get('completed_by', 'Unknown'),
                            'Task_ID': task.get('id')
                        })

    if not records:
        logger.warning("No labeled segments found in export.")
        return None

    df = pd.DataFrame(records)
    
    # Sort for cleanliness
    df = df.sort_values(by=['Group', 'Date', 'MouseID', 'Rub_Start_Time'])
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully saved export to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to save CSV: {e}")
        return None
