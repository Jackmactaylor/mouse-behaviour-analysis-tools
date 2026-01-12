import cv2
import numpy as np
from typing import List, Tuple, Dict

def detect_motion(video_path: str, sample_rate: int = 5) -> List[Tuple[float, float]]:
    """
    Scans a video and calculates a motion score for sampled frames.

    Args:
        video_path: Path to the video file.
        sample_rate: Process every Nth frame (default 5). 
                     Comparing frame T and T+sample_rate detects movement over that interval.

    Returns:
        List of (timestamp_seconds, motion_score) tuples.
        motion_score is the number of pixels that changed significantly.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    motion_data = []
    prev_frame = None
    
    # Get FPS to calculate timestamps
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0 # Fallback

    frame_idx = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Process only every Nth frame
            if frame_idx % sample_rate == 0:
                # 1. Convert to Grayscale
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # 2. Blur to remove noise (kernel size 21x21 is standard for this)
                gray = cv2.GaussianBlur(gray, (21, 21), 0)

                if prev_frame is None:
                    prev_frame = gray
                    frame_idx += 1
                    continue

                # 3. Calculate difference between current sampled frame and previous sampled frame
                frame_delta = cv2.absdiff(prev_frame, gray)
                
                # 4. Threshold (25 is a common threshold for pixel intensity change)
                thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
                
                # 5. Dilate to fill in holes
                thresh = cv2.dilate(thresh, None, iterations=2)

                # 6. Calculate score (number of non-zero pixels)
                score = np.count_nonzero(thresh)
                
                timestamp = frame_idx / fps
                motion_data.append((timestamp, float(score)))
                
                prev_frame = gray

            frame_idx += 1
    finally:
        cap.release()
        
    return motion_data

def generate_segments(motion_data: List[Tuple[float, float]], threshold: float = 500.0, min_duration: float = 1.0, merge_gap: float = 2.0) -> List[Dict]:
    """
    Converts raw motion scores into discrete time segments of activity.

    Args:
        motion_data: List of (timestamp, score) tuples.
        threshold: Minimum motion score to be considered "moving".
        min_duration: Minimum duration (seconds) for a segment to be kept.
        merge_gap: Maximum gap (seconds) between segments to merge them.

    Returns:
        List of dictionaries: [{'start': 10.5, 'end': 15.2, 'label': 'Active'}, ...]
    """
    if not motion_data:
        return []

    raw_segments = []
    current_start = None
    
    # 1. Identify all frames above threshold
    # We assume motion_data is sorted by timestamp
    for i, (ts, score) in enumerate(motion_data):
        is_active = score > threshold
        
        if is_active:
            if current_start is None:
                current_start = ts
        else:
            if current_start is not None:
                # End of a segment
                # Use the previous timestamp as end, or current? 
                # Current ts is the first INACTIVE frame, so it's a good end point.
                raw_segments.append({'start': current_start, 'end': ts})
                current_start = None
    
    # Handle case where video ends while active
    if current_start is not None:
        raw_segments.append({'start': current_start, 'end': motion_data[-1][0]})

    if not raw_segments:
        return []

    # 2. Merge segments that are close together
    merged_segments = []
    if raw_segments:
        current_seg = raw_segments[0]
        
        for next_seg in raw_segments[1:]:
            gap = next_seg['start'] - current_seg['end']
            
            if gap <= merge_gap:
                # Merge
                current_seg['end'] = next_seg['end']
            else:
                # Save current and start new
                merged_segments.append(current_seg)
                current_seg = next_seg
        
        merged_segments.append(current_seg)

    # 3. Filter by minimum duration and format
    final_segments = []
    for seg in merged_segments:
        duration = seg['end'] - seg['start']
        if duration >= min_duration:
            final_segments.append({
                'start': round(seg['start'], 2),
                'end': round(seg['end'], 2),
                'label': 'Active'
            })

    return final_segments
