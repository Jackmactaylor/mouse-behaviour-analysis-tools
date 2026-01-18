import ffmpeg
import os
import sys
import re
import json
import subprocess
import concurrent.futures
import threading
try:
    from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
except ImportError:
    try:
        from streamlit.scriptrunner import add_script_run_ctx, get_script_run_ctx
    except ImportError:
        add_script_run_ctx = None
        get_script_run_ctx = None

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

def _process_single_roi(
    roi_index: int,
    total_rois: int,
    input_path: str,
    roi: tuple,
    output_path: str,
    mouse_id: str,
    date: str,
    treatment: str,
    group: str,
    has_audio: bool,
    total_duration: float,
    progress_dict: Dict[int, float],
    progress_callback: Optional[Callable[[float, str], None]],
    script_run_ctx: Optional[object] = None
) -> str:
    """Helper function to process a single ROI in a thread."""
    if add_script_run_ctx and script_run_ctx:
        add_script_run_ctx(threading.current_thread(), script_run_ctx)
        
    try:
        x, y, w, h = roi
        
        # Determine safest fast settings for CPU since GPU passthrough is complex
        output_kwargs = {
            'vcodec': 'libx264', 
            'acodec': 'aac', 
            'preset': 'veryfast',  # Faster encoding
            'crf': 23,
            'threads': 4 # Allow each process to use 4 threads (16 total on 24 core CPU)
        }

        input_stream = ffmpeg.input(input_path)
        video_stream = input_stream.filter('crop', w, h, x, y)

        if has_audio:
            audio_stream = input_stream.audio
            stream = ffmpeg.output(video_stream, audio_stream, output_path, **output_kwargs)
        else:
            audio_stream = ffmpeg.input('anullsrc=channel_layout=stereo:sample_rate=44100', format='lavfi')
            output_kwargs['shortest'] = None
            stream = ffmpeg.output(video_stream, audio_stream, output_path, **output_kwargs)

        stream = stream.overwrite_output()
        args = ffmpeg.get_args(stream)
        cmd = ['ffmpeg'] + args
        
        # Run process
        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)
        
        # Monitor progress
        for line in process.stderr:
            if total_duration > 0:
                time_match = re.search(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})", line)
                if time_match:
                    hours, minutes, seconds = map(float, time_match.groups())
                    current_time = hours * 3600 + minutes * 60 + seconds
                    roi_progress = min(current_time / total_duration, 1.0)
                    
                    # Update shared dict
                    progress_dict[roi_index] = roi_progress
                    
                    # Compute global progress
                    if progress_callback:
                        avg_progress = sum(progress_dict.values()) / total_rois
                        progress_callback(avg_progress, f"Parallel Processing: {int(avg_progress*100)}%")

        process.wait()

        if process.returncode == 0:
            # Create JSON sidecar
            filename = os.path.basename(output_path)
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
            return output_path
        else:
            print(f"FFmpeg failed for ROI {roi_index}")
            return None

    except Exception as e:
        print(f"Error processing ROI {roi_index}: {e}")
        return None

def crop_video(input_path: str, rois: List[tuple], output_dir: str, metadata: Dict, progress_callback: Optional[Callable[[float, str], None]] = None) -> List[str]:
    """
    Crops a video into 4 separate files based on ROIs using parallel processing.
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

    # Capture streamlit context
    script_run_ctx = None
    if get_script_run_ctx:
        try:
            script_run_ctx = get_script_run_ctx()
        except:
            pass
    
    # Shared progress dictionary for threads
    progress_dict = {i: 0.0 for i in range(len(rois))}
    
    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(rois)) as executor:
        for i, roi in enumerate(rois):
            if i >= len(mouse_ids):
                mouse_id = f"Mouse{i+1}"
            else:
                mouse_id = mouse_ids[i]
            
            safe_mouse_id = "".join(c for c in mouse_id if c.isalnum() or c in ('-', '_'))
            filename = f"{safe_mouse_id}_{safe_date}_{safe_treatment}.mp4"
            output_path = os.path.join(target_dir, filename)
            
            future = executor.submit(
                _process_single_roi,
                i, len(rois), input_path, roi, output_path,
                mouse_id, date, treatment, group,
                has_audio, total_duration,
                progress_dict, progress_callback,
                script_run_ctx
            )
            futures.append(future)
            
        # Collect results
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                generated_files.append(result)
            
    return sorted(generated_files)

def generate_audio_proxy(input_path: str, output_path: str) -> bool:
    """
    Generates a lightweight audio proxy (MP3) for a video file.
    Used by Label Studio to render the waveform without loading the full video.
    
    Args:
        input_path: Path to the source video.
        output_path: Path where the MP3 should be saved.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Check if output already exists
        if os.path.exists(output_path):
            return True
            
        print(f"Generating audio proxy for {input_path} -> {output_path}")
        
        # Check for audio stream first
        if has_audio_stream(input_path):
            # Extract audio: -vn (no video), -ac 1 (mono), -ar 44100, -b:a 64k (low bitrate)
            # using -y to overwrite
            cmd = [
                "ffmpeg", "-y",
                "-i", input_path,
                "-vn",
                "-ac", "1",
                "-ar", "44100",
                "-b:a", "64k",
                output_path
            ]
        else:
            # Generate silence matching duration
            duration = get_video_duration(input_path)
            if duration <= 0:
                duration = 10 # Fallback
                
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", "anullsrc=r=44100:cl=mono",
                "-t", str(duration),
                "-b:a", "64k",
                output_path
            ]
            
        # Run command
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            print(f"FFmpeg Error: {result.stderr}")
            return False
            
        return True
        
    except Exception as e:
        print(f"Error generating audio proxy: {e}")
        return False

def generate_video_proxy(input_path: str, output_path: str, height: int = 720, crf: int = 26, progress_callback: Optional[Callable[[float], None]] = None) -> bool:
    """
    Generates a web-optimized, smaller video proxy for labelling.
    Resizes, compresses, removes audio, and adds faststart flags.
    
    Args:
        input_path: Path to source video.
        output_path: Path to save proxy.
        height: Target height (default 720p). Width is auto-scaled.
        crf: Constant Rate Factor (18-28). Higher = lower quality/size.
        progress_callback: Optional callback receiving float 0.0-1.0.
        
    Returns:
        bool: True if successful.
    """
    try:
        # Check if output exists. Note: In a real scenarios, you might want to overwrite if settings changed.
        # But for valid cache, we skip.
        if os.path.exists(output_path):
            if progress_callback: progress_callback(1.0)
            return True
            
        print(f"Generating video proxy for {input_path} -> {output_path}")

        # ffmpeg -i input -vf scale=-2:720 -c:v libx264 -crf 26 -preset veryfast -an -movflags +faststart output
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", f"scale=-2:{height}",
            "-c:v", "libx264",
            "-crf", str(crf),
            "-preset", "veryfast",
            "-an", # Remove audio (we use separate audio proxy)
            "-movflags", "+faststart",
            output_path
        ]
        
        if progress_callback:
            total_duration = get_video_duration(input_path)
            # Use machine-readable progress on stdout
            cmd.extend(["-progress", "pipe:1"])
            
            # Start process
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            while True:
                line = process.stdout.readline()
                if not line:
                    if process.poll() is not None:
                        break
                    continue
                
                line = line.strip()
                if "=" in line:
                    key, value = line.split("=", 1)
                    if key == "out_time_us":
                        try:
                            # out_time_us is in microseconds
                            us = int(value)
                            current_seconds = us / 1_000_000.0
                            if total_duration > 0:
                                progress = min(1.0, current_seconds / total_duration)
                                progress_callback(progress)
                        except ValueError:
                            pass

            # Wait for finish
            process.wait()
            
            if process.returncode != 0:
                # Read stderr for error details
                err = process.stderr.read()
                print(f"FFmpeg Error (Video Proxy): {err}")
                return False
            return True
            
        else:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                print(f"FFmpeg Error (Video Proxy): {result.stderr}")
                return False
            return True

    except Exception as e:
        print(f"Error generating video proxy: {e}")
        return False

