import ffmpeg
import os
import sys
import re
import json
import subprocess
from typing import List, Dict, Callable, Optional

def get_video_duration(input_path: str) -> float:
    """Returns the duration of the video in seconds."""
    try:
        probe = ffmpeg.probe(input_path)
        return float(probe['format']['duration'])
    except (ffmpeg.Error, KeyError, ValueError):
        return 0.0

def get_video_fps(input_path: str) -> float:
    """Returns the framerate of the video."""
    try:
        probe = ffmpeg.probe(input_path)
        # Try to get r_frame_rate from the first video stream
        streams = probe.get('streams', [])
        for stream in streams:
            if stream['codec_type'] == 'video':
                r_frame_rate = stream.get('r_frame_rate')
                if r_frame_rate:
                    num, den = map(int, r_frame_rate.split('/'))
                    return num / den if den != 0 else 0.0
        return 0.0
    except (ffmpeg.Error, KeyError, ValueError, IndexError, ZeroDivisionError):
        return 0.0

def has_audio_stream(input_path: str) -> bool:
    """Checks if the video has an audio stream."""
    try:
        probe = ffmpeg.probe(input_path)
        for stream in probe.get('streams', []):
            if stream['codec_type'] == 'audio':
                return True
        return False
    except (ffmpeg.Error, KeyError, ValueError):
        return False

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
    generated_files = []
    
    mouse_ids = metadata.get("mouse_ids", ["Unknown"] * 4)
    date = metadata.get("date", "UnknownDate")
    treatment = metadata.get("treatment", "UnknownTreatment")
    group = metadata.get("group", "UnknownGroup")
    
    total_duration = get_video_duration(input_path)

    # Sanitize metadata for paths
    safe_date = "".join(c for c in date if c.isalnum() or c in ('-', '_'))
    safe_treatment = "".join(c for c in treatment if c.isalnum() or c in ('-', '_'))
    safe_group = "".join(c for c in group if c.isalnum() or c in ('-', '_'))

    # Create structured output directory: output_dir / date / group_treatment
    sub_dir_name = f"{safe_group}_{safe_treatment}"
    target_dir = os.path.join(output_dir, safe_date, sub_dir_name)
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # Check for audio once
    has_audio = has_audio_stream(input_path)

    for i, roi in enumerate(rois):
        if i >= len(mouse_ids):
            mouse_id = f"Mouse{i+1}"
        else:
            mouse_id = mouse_ids[i]

        x, y, w, h = roi
        
        safe_mouse_id = "".join(c for c in mouse_id if c.isalnum() or c in ('-', '_'))
        
        filename = f"{safe_mouse_id}_{safe_date}_{safe_treatment}.mp4"
        output_path = os.path.join(target_dir, filename)
        
        msg = f"Processing ROI {i+1}/{len(rois)}: {filename}"
        print(msg)
        sys.stdout.flush()
        
        if progress_callback:
            # Base progress for this ROI (e.g. 0.0, 0.25, 0.5, 0.75)
            base_progress = i / len(rois)
            progress_callback(base_progress, msg)
        
        try:
            # Build FFmpeg command manually to read stderr line-by-line
            input_stream = ffmpeg.input(input_path)
            video_stream = input_stream.filter('crop', w, h, x, y)
            
            output_kwargs = {
                'vcodec': 'libx264', 
                'acodec': 'aac', 
                'preset': 'fast', 
                'crf': 23
            }

            if has_audio:
                # Map existing audio
                audio_stream = input_stream.audio
                stream = ffmpeg.output(video_stream, audio_stream, output_path, **output_kwargs)
            else:
                # Generate silent audio to satisfy Label Studio's timeline requirement
                audio_stream = ffmpeg.input('anullsrc=channel_layout=stereo:sample_rate=44100', format='lavfi')
                # Use shortest=None to add -shortest flag, ensuring audio stops with video
                output_kwargs['shortest'] = None
                stream = ffmpeg.output(video_stream, audio_stream, output_path, **output_kwargs)

            stream = stream.overwrite_output()
            
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
                
                # Create JSON sidecar
                sidecar_path = output_path.replace('.mp4', '.json')
                sidecar_data = {
                    "original_file": input_path,
                    "mouse_id": mouse_id,
                    "date": date,
                    "treatment": treatment,
                    "group": group,
                    "roi": roi,
                    "processed_file": filename
                }
                with open(sidecar_path, 'w') as f:
                    json.dump(sidecar_data, f, indent=2)
            else:
                print(f"FFmpeg failed for ROI {i}")
                
        except Exception as e:
            error_msg = f"Error processing ROI {i}: {e}"
            print(error_msg)
            sys.stdout.flush()
            if progress_callback:
                progress_callback(base_progress, f"❌ {error_msg}")
            
    return generated_files
