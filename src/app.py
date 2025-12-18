import streamlit as st
import subprocess
import os
import sys
import cv2
import glob
import json

# Add current directory to path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from utils.metadata import parse_video_path, load_group_map
    from utils.video_processor import crop_video, get_video_fps
    from components.roi_selector import render_roi_selector
    from utils.label_studio import LabelStudioClient
    from components.label_studio_config import LABEL_STUDIO_CONFIG, PROJECT_TITLE
except ImportError as e:
    st.error(f"Import Error: {e}. Please ensure you are running from the correct directory.")

st.set_page_config(page_title="Mouse Behavior Analysis", page_icon="🐭", layout="wide")

st.title("🐭 Mouse Behavior Analysis Pipeline")

st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Ingestion", "Labelling Queue", "System Check"])

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
        
        st.info("👉 Go to the 'Labelling Queue' page to push these videos to Label Studio.")

        if st.button("Process Another Video"):
            st.session_state.processed_files = []
            st.rerun()

# --- LABELLING QUEUE PAGE ---
elif page == "Labelling Queue":
    st.header("Labelling Queue")
    st.markdown("Manage processed videos and push them to Label Studio.")
    
    processed_dir = "/workspace/processed"
    
    # 1. Scan for Processed Videos (JSON sidecars)
    found_videos = []
    if os.path.exists(processed_dir):
        for root, dirs, files in os.walk(processed_dir):
            for file in files:
                if file.endswith(".json"):
                    json_path = os.path.join(root, file)
                    try:
                        with open(json_path, 'r') as f:
                            meta = json.load(f)
                            # Verify the video file exists
                            video_filename = meta.get("processed_file")
                            if video_filename:
                                video_path = os.path.join(root, video_filename)
                                if os.path.exists(video_path):
                                    found_videos.append({
                                        "path": video_path,
                                        "meta": meta,
                                        "rel_path": os.path.relpath(video_path, processed_dir)
                                    })
                    except Exception as e:
                        st.warning(f"Error reading {file}: {e}")
    
    if not found_videos:
        st.info("No processed videos found. Go to 'Ingestion' to process raw videos.")
    else:
        st.write(f"Found {len(found_videos)} processed videos.")
        
        # 2. Selection Table
        # Create a dataframe-like structure for display
        import pandas as pd
        
        data = []
        for v in found_videos:
            m = v["meta"]
            data.append({
                "Select": False,
                "Mouse ID": m.get("mouse_id"),
                "Date": m.get("date"),
                "Treatment": m.get("treatment"),
                "Group": m.get("group"),
                "File": m.get("processed_file")
            })
            
        df = pd.DataFrame(data)
        
        # Use Streamlit's data editor for selection (requires Streamlit 1.23+)
        # Since we are on 1.29, this is perfect.
        edited_df = st.data_editor(
            df,
            column_config={
                "Select": st.column_config.CheckboxColumn(
                    "Select",
                    help="Select to upload",
                    default=False,
                )
            },
            disabled=["Mouse ID", "Date", "Treatment", "Group", "File"],
            hide_index=True,
        )
        
        # Get selected rows
        selected_rows = edited_df[edited_df.Select]
        
        st.divider()
        
        # 3. Push to Label Studio
        st.subheader("Push to Label Studio")
        
        st.info("Authentication is handled automatically via system credentials.")

        if not selected_rows.empty:
            st.write(f"Selected {len(selected_rows)} videos for upload.")
            
            if st.button("🚀 Upload Selected Tasks"):
                try:
                    # Initialize client with env vars (username/password)
                    ls_client = LabelStudioClient(
                        username=os.getenv("LABEL_STUDIO_USERNAME"),
                        password=os.getenv("LABEL_STUDIO_PASSWORD")
                    )
                    
                    is_connected, error_msg = ls_client.check_connection()
                    
                    if is_connected:
                        project_id = ls_client.get_or_create_project(PROJECT_TITLE, LABEL_STUDIO_CONFIG)
                        
                        # Ensure Local Storage is configured
                        # We use /label-studio/files as the storage path because DOCUMENT_ROOT is /
                        ls_client.create_local_storage(project_id, "/label-studio/files")
                        
                        tasks = []
                        # Match selected rows back to found_videos
                        # We can use the 'File' column (filename) as a key, assuming uniqueness within the list
                        # Or better, iterate through found_videos and check if they are in selected_rows
                        
                        selected_filenames = selected_rows["File"].tolist()
                        
                        for v in found_videos:
                            if v["meta"].get("processed_file") in selected_filenames:
                                # Construct Task
                                rel_path = v["rel_path"].replace(os.sep, '/')
                                # Use path relative to DOCUMENT_ROOT (which is /)
                                # So we prepend label-studio/files/
                                video_url = f"/data/local-files/?d=label-studio/files/{rel_path}"
                                
                                # Calculate FPS
                                fps = get_video_fps(v["path"])
                                if fps == 0:
                                    st.warning(f"Could not detect FPS for {v['meta'].get('processed_file')}. Defaulting to 60.0.")
                                    fps = 60.0 # Default fallback
                                
                                task = {
                                    "video": video_url,
                                    "fps": fps,
                                    "meta": v["meta"]
                                }
                                tasks.append(task)
                                print(f"DEBUG: Task payload: {task}") # Log to console
                        
                        if tasks:
                            ls_client.import_tasks(project_id, tasks)
                            st.success(f"Successfully imported {len(tasks)} tasks to Project #{project_id}!")
                            st.markdown(f"[Open Label Studio](http://localhost:8080/projects/{project_id})")
                        else:
                            st.warning("No tasks generated. Something went wrong with matching selections.")
                            
                    else:
                        st.error(f"Could not connect to Label Studio: {error_msg}")
                        
                except Exception as e:
                    st.error(f"Upload failed: {e}")
        else:
            st.info("Select videos in the table above to enable upload.")

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
