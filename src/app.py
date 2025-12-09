import streamlit as st
import subprocess
import os
import sys
import cv2
import glob

# Add current directory to path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from utils.metadata import parse_video_path, load_group_map
    from utils.video_processor import crop_video
    from components.roi_selector import render_roi_selector
except ImportError as e:
    st.error(f"Import Error: {e}. Please ensure you are running from the correct directory.")

st.set_page_config(page_title="Mouse Behavior Analysis", page_icon="🐭", layout="wide")

st.title("🐭 Mouse Behavior Analysis Pipeline")

st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Ingestion", "System Check", "Processing (Coming Soon)"])

# --- INGESTION PAGE ---
if page == "Ingestion":
    st.header("Ingestion & Pre-processing")
    st.markdown("Select a raw video, define ROIs for each cage, and generate cropped clips.")

    # 1. Inbox Browser
    st.subheader("1. Select Video from Inbox")
    raw_dir = "/workspace/raw"
    processed_dir = "/workspace/processed"
    
    video_files = []
    if os.path.exists(raw_dir):
        # Recursive search for video files
        for root, dirs, files in os.walk(raw_dir):
            for file in files:
                if file.lower().endswith(('.mp4', '.m4v', '.mov', '.avi', '.mkv')):
                    # Store full path
                    video_files.append(os.path.join(root, file))
    
    if not video_files:
        st.warning(f"No video files found in `{raw_dir}`. Please copy files to the Staging Area.")
        st.stop()
        
    # Create a display list (relative paths) for the dropdown
    display_names = [os.path.relpath(f, raw_dir) for f in video_files]
    selected_index = st.selectbox("Select a video:", range(len(video_files)), format_func=lambda x: display_names[x])
    selected_video_path = video_files[selected_index]
    
    st.info(f"Selected: `{selected_video_path}`")

    # 2. Metadata
    st.subheader("2. Verify Metadata")

    # Check map file
    map_path = "/workspace/mouse_map.csv"
    if os.path.exists(map_path):
        st.caption(f"✅ Loaded configuration from `{map_path}`")
    else:
        st.warning(f"⚠️ Configuration file not found at `{map_path}`. Using internal defaults.")
    
    # Auto-parse metadata
    parsed_meta = parse_video_path(selected_video_path, root_dir=raw_dir)
    
    # Load Group Map for Dropdown
    group_map = load_group_map()
    group_options = ["Auto-Detect"] + list(group_map.keys())
    
    # Determine default index based on parsed group
    default_ix = 0
    parsed_group = parsed_meta.get("group")
    if parsed_group in group_map:
        default_ix = group_options.index(parsed_group)
        
    selected_group_option = st.selectbox("Select Group Template", group_options, index=default_ix)
    
    # Determine values to populate fields
    if selected_group_option != "Auto-Detect":
        # Use selected template
        group_val = selected_group_option
        treatment_val = group_map[selected_group_option]["treatment"]
        mouse_ids_val = group_map[selected_group_option]["cages"]
    else:
        # Use parsed values
        group_val = parsed_meta.get("group", "Unknown")
        treatment_val = parsed_meta.get("treatment", "Unknown")
        mouse_ids_val = parsed_meta.get("mouse_ids", ["", "", "", ""])

    # Use a key that includes the selected group to force refresh when template changes
    form_key_suffix = f"{selected_group_option}_{selected_video_path}"

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Experiment Details")
        group = st.text_input("Group", value=group_val, key=f"group_{form_key_suffix}")
        date = st.text_input("Date", value=parsed_meta.get("date", "Unknown"), key=f"date_{selected_video_path}")
        treatment = st.text_input("Treatment", value=treatment_val, key=f"treatment_{form_key_suffix}")
    with col2:
        st.markdown("### Mouse IDs (Cage 1-4)")
        m1 = st.text_input("Cage 1", value=mouse_ids_val[0], key=f"m1_{form_key_suffix}")
        m2 = st.text_input("Cage 2", value=mouse_ids_val[1], key=f"m2_{form_key_suffix}")
        m3 = st.text_input("Cage 3", value=mouse_ids_val[2], key=f"m3_{form_key_suffix}")
        m4 = st.text_input("Cage 4", value=mouse_ids_val[3], key=f"m4_{form_key_suffix}")
        
    final_metadata = {
        "group": group,
        "treatment": treatment,
        "date": date,
        "mouse_ids": [m1, m2, m3, m4]
    }

    # 3. ROI Selection
    st.divider()
    
    # Disable ROI selector if processing
    if st.session_state.get("processing_active", False):
        st.info("🔒 ROI Selection is hidden while processing is active. To cancel, refresh the page.")
        rois = st.session_state.get("current_rois")
    else:
        rois = render_roi_selector(selected_video_path)

    # 4. Processing
    st.divider()
    st.subheader("4. Process Video")
    
    # Initialize session state for processing
    if "processing_active" not in st.session_state:
        st.session_state.processing_active = False
    if "processed_files" not in st.session_state:
        st.session_state.processed_files = []

    if rois and len(rois) == 4:
        # Start Button
        if not st.session_state.processing_active:
            if st.button("✂️ Crop & Process", type="primary"):
                st.session_state.processing_active = True
                st.session_state.current_rois = rois  # Save ROIs to session state
                st.session_state.processed_files = [] # Clear previous results
                st.rerun()
        
        # Processing Block
        if st.session_state.processing_active:
            st.info("⏳ Processing started... Please do not refresh the page.")
            
            # Progress Bar
            progress_bar = st.progress(0.0)
            status_text = st.empty()
            
            def update_progress(prog, msg):
                # Ensure prog is between 0.0 and 1.0
                prog = max(0.0, min(1.0, prog))
                progress_bar.progress(prog)
                status_text.text(f"{msg} ({int(prog*100)}%)")
            
            try:
                output_files = crop_video(selected_video_path, rois, processed_dir, final_metadata, progress_callback=update_progress)
                
                st.session_state.processed_files = output_files
                st.session_state.processing_active = False
                st.rerun()
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.session_state.processing_active = False
                if st.button("Reset"):
                    st.rerun()

    else:
        st.warning("Please define exactly 4 ROIs above to enable processing.")

    # Display Results (Persistent)
    if st.session_state.processed_files:
        st.success("✅ Processing Complete!")
        st.write("Generated Files:")
        for f in st.session_state.processed_files:
            st.code(os.path.basename(f))
        
        if st.button("Process Another Video"):
            st.session_state.processed_files = []
            st.rerun()

# --- SYSTEM CHECK PAGE ---
elif page == "System Check":
    st.header("System Status Check")
    
    # 1. Check FFmpeg
    st.subheader("1. FFmpeg")
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            st.success("FFmpeg is installed and accessible.")
            with st.expander("Show FFmpeg version"):
                st.code(result.stdout.split('\n')[0])
        else:
            st.error("FFmpeg command failed.")
    except FileNotFoundError:
        st.error("FFmpeg binary not found.")

    # 2. Check OpenCV
    st.subheader("2. OpenCV")
    try:
        version = cv2.__version__
        st.success(f"OpenCV is importable. Version: {version}")
    except ImportError:
        st.error("Could not import cv2.")

    # 3. Check Workspace (Inbox)
    st.subheader("3. Workspace (Inbox)")
    workspace_path = "/workspace"
    
    if os.path.exists(workspace_path):
        st.success(f"Workspace found at `{workspace_path}`.")
        
        # Check Raw (Inbox)
        raw_path = os.path.join(workspace_path, "raw")
        if os.path.exists(raw_path):
            st.markdown(f"### 📥 Inbox (`/workspace/raw`)")
            files = []
            for root, _, filenames in os.walk(raw_path):
                for filename in filenames:
                    files.append(os.path.relpath(os.path.join(root, filename), raw_path))
            
            if len(files) > 0:
                st.write(f"Found {len(files)} files ready for processing:")
                st.code("\n".join(files))
            else:
                st.warning("Inbox is empty.")
        else:
            st.error("❌ `/workspace/raw` missing")

        # Check Processed
        processed_path = os.path.join(workspace_path, "processed")
        if os.path.exists(processed_path):
             st.markdown(f"### 📤 Processed (`/workspace/processed`)")
             st.write("Cropped videos will appear here.")
        else:
             st.error("❌ `/workspace/processed` missing")
             
    else:
        st.error(f"Workspace not found at `{workspace_path}`.")

elif page == "Processing (Coming Soon)":
    st.info("This module will handle motion heuristics and analysis.")
