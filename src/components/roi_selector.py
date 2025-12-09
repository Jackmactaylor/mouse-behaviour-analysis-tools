import streamlit as st
from streamlit_drawable_canvas import st_canvas
import cv2
import numpy as np
from PIL import Image
import os

def get_video_frame(video_path, frame_number=0):
    """Extracts a specific frame from a video."""
    if not os.path.exists(video_path):
        return None
        
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = cap.read()
    cap.release()
    
    if ret:
        # Convert BGR to RGB
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return None

def get_total_frames(video_path):
    """Returns the total number of frames in the video."""
    if not os.path.exists(video_path):
        return 0
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return total

def render_roi_selector(video_path, key="roi_canvas"):
    """
    Renders the ROI selector component.
    Returns a list of 4 ROIs [x, y, w, h] scaled to the original video resolution, 
    or None if not confirmed/incomplete.
    """
    st.subheader("Draw 4 ROIs (One for each cage)")
    st.markdown("Draw a box around each mouse cage. The order usually matters (e.g. Top-Left, Top-Right, Bottom-Left, Bottom-Right).")

    # Frame Selection
    total_frames = get_total_frames(video_path)
    if total_frames > 0:
        frame_index = st.slider("Select Frame (find a clear view of all cages)", 0, total_frames - 1, 0)
    else:
        frame_index = 0

    # 1. Get Frame
    frame = get_video_frame(video_path, frame_number=frame_index)
    if frame is None:
        st.error(f"Could not load video: {video_path}")
        return None

    # 2. Display Canvas
    # Resize frame for display if it's too large, but keep aspect ratio
    # For simplicity, let's display at a fixed width and scale coordinates back
    display_width = 700
    original_height, original_width, _ = frame.shape
    scale_factor = original_width / display_width
    display_height = int(original_height / scale_factor)
    
    frame_image = Image.fromarray(frame).resize((display_width, display_height))
    
    # Create a canvas component
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
        stroke_width=2,
        stroke_color="#FF0000",
        background_image=frame_image,
        update_streamlit=True,
        height=display_height,
        width=display_width,
        drawing_mode="rect",
        key=key,
    )

    # 3. Process Results
    rois = []
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data["objects"]
        for obj in objects:
            if obj["type"] == "rect":
                # Scale back to original resolution
                x = int(obj["left"] * scale_factor)
                y = int(obj["top"] * scale_factor)
                w = int(obj["width"] * scale_factor)
                h = int(obj["height"] * scale_factor)
                rois.append((x, y, w, h))

    st.write(f"Selected ROIs: {len(rois)}")
    
    if len(rois) == 4:
        st.success("4 ROIs selected!")
        return rois
    elif len(rois) > 4:
        st.warning("You have selected more than 4 ROIs. Please remove extras.")
        return None
    else:
        st.info(f"Please select {4 - len(rois)} more ROIs.")
        return None
