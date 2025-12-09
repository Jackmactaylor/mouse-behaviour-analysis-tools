import ffmpeg
import os
import sys
import re
import subprocess
from typing import List, Dict, Callable, Optional

def get_video_duration(input_path: str) -> float:
    """Returns the duration of the video in seconds."""
    try:
        probe = ffmpeg.probe(input_path)
        return float(probe['format']['duration'])
    except (ffmpeg.Error, KeyError, ValueError):
        return 0.0

def crop_video(input_path: str, rois: List[tuple], output_dir: str, metadata: Dict, progress_callback: Optional[Callable[[float, str], None]] = None) -> List[str]:
    """
    Crops a video into 4 separate files based on ROIs.
    
    Args:
        input_path: Path to source video.
        rois: List of 4 tuples (x, y, w, h).
        output_dir: Directory to save outputs.
        metadata: Dictionary containing 'mouse_ids', 'date', 'treatment'.
        progress_callback: Optional function to report progress (0.0-1.0) and message.
    
    Returns:
        List of paths to generated files.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    generated_files = []
    
    mouse_ids = metadata.get("mouse_ids", ["Unknown"] * 4)
    date = metadata.get("date", "UnknownDate")
    treatment = metadata.get("treatment", "UnknownTreatment")
    
    total_duration = get_video_duration(input_path)

    for i, roi in enumerate(rois):
        if i >= len(mouse_ids):
            mouse_id = f"Mouse{i+1}"
        else:
            mouse_id = mouse_ids[i]

        x, y, w, h = roi
        
        safe_mouse_id = "".join(c for c in mouse_id if c.isalnum() or c in ('-', '_'))
        safe_date = "".join(c for c in date if c.isalnum() or c in ('-', '_'))
        safe_treatment = "".join(c for c in treatment if c.isalnum() or c in ('-', '_'))
        
        filename = f"{safe_mouse_id}_{safe_date}_{safe_treatment}.mp4"
        output_path = os.path.join(output_dir, filename)
        
        msg = f"Processing ROI {i+1}/{len(rois)}: {filename}"
        print(msg)
        sys.stdout.flush()
        
        if progress_callback:
            # Base progress for this ROI (e.g. 0.0, 0.25, 0.5, 0.75)
            base_progress = i / len(rois)
            progress_callback(base_progress, msg)
        
        try:
            # Build FFmpeg command manually to read stderr line-by-line
            stream = (
                ffmpeg
                .input(input_path)
                .filter('crop', w, h, x, y)
                .output(output_path, vcodec='libx264', acodec='aac', preset='fast', crf=23)
                .overwrite_output()
            )
            args = ffmpeg.get_args(stream)
            cmd = ['ffmpeg'] + args
            
            process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)
            
            # Read stderr for progress
            for line in process.stderr:
                if progress_callback and total_duration > 0:
                    # Look for time=00:00:00.00
                    time_match = re.search(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})", line)
                    if time_match:
                        hours, minutes, seconds = map(float, time_match.groups())
                        current_time = hours * 3600 + minutes * 60 + seconds
                        # Calculate progress for this specific ROI (0.0 to 1.0)
                        roi_progress = min(current_time / total_duration, 1.0)
                        # Map to total progress (e.g. if ROI 1 is 50% done, total is 12.5%)
                        total_progress = base_progress + (roi_progress / len(rois))
                        progress_callback(total_progress, msg)
            
            process.wait()
            
            if process.returncode == 0:
                generated_files.append(output_path)
            else:
                print(f"FFmpeg failed for ROI {i}")
                
        except Exception as e:
            error_msg = f"Error processing ROI {i}: {e}"
            print(error_msg)
            sys.stdout.flush()
            if progress_callback:
                progress_callback(base_progress, f"❌ {error_msg}")
            
    return generated_files
