import streamlit as st
import subprocess
import os
import sys
import cv2
import glob
import json
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

# Add current directory to path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from utils.metadata import parse_video_path, load_group_map
    from utils.video_processor import crop_video, get_video_fps, get_video_duration, generate_audio_proxy, generate_video_proxy
    from components.roi_selector import render_roi_selector
    from utils.label_studio import LabelStudioClient
    from utils.data_exporter import process_export_to_csv
    from components.label_studio_config import LABEL_STUDIO_CONFIG, PROJECT_TITLE, LABEL_STUDIO_MULTI_CONFIG, PROJECT_TITLE_MULTI
    from utils.motion import detect_motion, generate_segments
except ImportError as e:
    st.error(f"Import Error: {e}. Please ensure you are running from the correct directory.")

st.set_page_config(page_title="Mouse Behavior Analysis", page_icon="🐭", layout="wide")

st.title("🐭 Mouse Behavior Analysis Pipeline")

st.label_studio_url = os.getenv("LABEL_STUDIO_URL", "http://label-studio:8080")

st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Ingestion", "ROI Processing", "Labelling Queue", "Data Export", "System Check"])

# --- INGESTION PAGE ---
if page == "Ingestion":
    st.header("Ingestion (Metadata Registration)")
    st.markdown("Register raw videos by verifying their metadata. This makes them available for labelling or optional cropping.")

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
        "mouse_ids": [m1, m2, m3, m4],
        "original_file": os.path.basename(selected_video_path),
        "full_path": selected_video_path # Keep for reference
    }

    # 3. Registration
    st.divider()
    st.subheader("3. Register Video")
    
    if st.button("💾 Save Metadata & Register", type="primary"):
        try:
            # Create artifact folder: video.mp4 -> video/video.json
            base_name = os.path.basename(selected_video_path)
            file_name_no_ext = os.path.splitext(base_name)[0]
            parent_dir = os.path.dirname(selected_video_path)
            
            artifact_dir = os.path.join(parent_dir, file_name_no_ext)
            os.makedirs(artifact_dir, exist_ok=True)
            
            json_path = os.path.join(artifact_dir, file_name_no_ext + ".json")
            
            with open(json_path, 'w') as f:
                json.dump(final_metadata, f, indent=2)
                
            st.success(f"Video registered! Metadata saved to `{os.path.relpath(json_path, raw_dir)}`.")
            st.info("You can now find this video in the 'Labelling Queue' or 'ROI Processing'.")
            
        except Exception as e:
            st.error(f"Failed to save metadata: {e}")

# --- ROI PROCESSING PAGE ---
elif page == "ROI Processing":
    st.header("ROI Processing (Optional)")
    st.markdown("Select a **registered** video, define ROIs, and generate individual cropped clips.")
    
    raw_dir = "/workspace/raw"
    processed_dir = "/workspace/processed"
    
    # 1. Scan for Registered Videos (files with JSON sidecars)
    registered_videos = []
    if os.path.exists(raw_dir):
        for root, dirs, files in os.walk(raw_dir):
            for file in files:
                if file.lower().endswith(('.mp4', '.m4v', '.mov', '.avi', '.mkv')):
                    video_path = os.path.join(root, file)
                    base, _ = os.path.splitext(video_path)
                    
                    # Check for legacy sidecar (video.json) or new folder sidecar (video/video.json)
                    json_path_legacy = base + ".json"
                    
                    file_name_no_ext = os.path.splitext(file)[0]
                    json_path_folder = os.path.join(root, file_name_no_ext, file_name_no_ext + ".json")
                    
                    final_json_path = None
                    if os.path.exists(json_path_folder):
                        final_json_path = json_path_folder
                    elif os.path.exists(json_path_legacy):
                        final_json_path = json_path_legacy
                    
                    if final_json_path:
                        try:
                            with open(final_json_path, 'r') as f:
                                meta = json.load(f)
                                registered_videos.append({
                                    "path": video_path,
                                    "meta": meta,
                                    "rel_path": os.path.relpath(video_path, raw_dir)
                                })
                        except Exception:
                            logger.debug(f"Failed to parse JSON sidecar: {final_json_path}")

    if not registered_videos:
        st.warning("No registered videos found. Please go to **Ingestion** to register videos first.")
        st.stop()
        
    # Selection Dropdown
    display_names = [f"{v['rel_path']} ({v['meta'].get('group', '?')})" for v in registered_videos]
    selected_idx = st.selectbox("Select a registered video:", range(len(registered_videos)), format_func=lambda x: display_names[x])
    
    selected_video_obj = registered_videos[selected_idx]
    selected_video_path = selected_video_obj["path"]
    final_metadata = selected_video_obj["meta"]
    
    st.info(f"Selected: `{selected_video_path}`")
    st.json(final_metadata, expanded=False)

    # 2. ROI Selection
    st.divider()
    
    # Disable ROI selector if processing
    if st.session_state.get("processing_active", False):
        st.info("🔒 ROI Selection is hidden while processing is active. To cancel, refresh the page.")
        rois = st.session_state.get("current_rois")
    else:
        rois = render_roi_selector(selected_video_path)

    # 3. Processing

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
    st.markdown("Manage videos and push them to Label Studio.")
    
    tab1, tab2 = st.tabs(["Raw Videos (Multi-Mouse)", "Processed Clips (Single Mouse)"])
    
    # --- TAB 1: RAW VIDEOS ---
    with tab1:
        st.subheader("Raw Videos (Full Frame)")
        raw_dir = "/workspace/raw"
        
        # Scan for Registered Videos
        raw_videos = []
        if os.path.exists(raw_dir):
            for root, dirs, files in os.walk(raw_dir):
                for file in files:
                    # Look for sidecar JSONs
                    if file.endswith(".json"):
                        json_path = os.path.join(root, file)
                        try:
                            with open(json_path, 'r') as f:
                                meta = json.load(f)
                                # Check if this is a registered raw video (has original_file key)
                                if "original_file" in meta:
                                    vid_file = meta["original_file"]
                                    # Fallback if original_file is just filename, check path
                                    full_vid_path = meta.get("full_path")
                                    
                                    # Logic to find the video if full_path is outdated or relative
                                    # If JSON is in raw/Video/Video.json, root is raw/Video
                                    # Video might be in raw/Video.mp4 (parent of root)
                                    if not full_vid_path or not os.path.exists(full_vid_path):
                                        # Check same dir
                                        check_1 = os.path.join(root, vid_file)
                                        # Check parent dir
                                        check_2 = os.path.join(os.path.dirname(root), vid_file)
                                        
                                        if os.path.exists(check_1):
                                            full_vid_path = check_1
                                        elif os.path.exists(check_2):
                                            full_vid_path = check_2

                                    if full_vid_path and os.path.exists(full_vid_path):
                                        raw_videos.append({
                                            "path": full_vid_path,
                                            "meta": meta,
                                            "rel_path": os.path.relpath(full_vid_path, raw_dir),
                                            "json_dir": root # Tracking where the JSON lives for artifact storage
                                        })
                        except Exception:
                            logger.debug(f"Failed to parse JSON sidecar: {json_path}")

        if not raw_videos:
            st.info("No registered raw videos found.")
        else:
            # Table
            data_raw = []
            for v in raw_videos:
                m = v["meta"]
                data_raw.append({
                    "Select": False,
                    "Group": m.get("group"),
                    "Date": m.get("date"),
                    "Mice": str(m.get("mouse_ids")),
                    "File": os.path.basename(v["path"])
                })
            
            df_raw = pd.DataFrame(data_raw)
            edited_df_raw = st.data_editor(df_raw, column_config={"Select": st.column_config.CheckboxColumn("Select", default=False)}, hide_index=True, key="editor_raw")
            selected_raw = edited_df_raw[edited_df_raw.Select]
            
            if not selected_raw.empty:
                # Options
                use_proxy = st.checkbox("Generate Optimized Video Proxy (Recommended for slow connections)", value=True, help="Creates a compressed 720p version of the video for faster loading. Requires valid FFmpeg.")
                force_reprocess = st.checkbox("Force Reprocess Proxies", value=False, help="Re-generate proxy files even if they already exist. Use if proxies are corrupted.")
                
                if st.button("🚀 Upload Raw Videos to Label Studio"):
                    ls_client = LabelStudioClient(username=os.getenv("LABEL_STUDIO_USERNAME"), password=os.getenv("LABEL_STUDIO_PASSWORD"))
                    if ls_client.check_connection()[0]:
                        # Use MULTI config
                        project_id = ls_client.get_or_create_project(PROJECT_TITLE_MULTI, LABEL_STUDIO_MULTI_CONFIG)
                        
                        # Ensure /label-studio/raw is registered as storage source
                        ls_client.create_local_storage(project_id, "/label-studio/raw", title="Raw Videos")
                        
                        # Creating tasks...
                        status_text = st.empty()
                        progress_bar = st.progress(0.0)
                        count = 0 
                        total_items = len(selected_raw)
                        
                        for i, (idx, row) in enumerate(selected_raw.iterrows()):
                             # Find original vid object
                             fname = row["File"]
                             v_obj = next((v for v in raw_videos if os.path.basename(v["path"]) == fname), None)
                             if v_obj:
                                 status_text.text(f"Processing ({i+1}/{total_items}): {fname}...")
                                 
                                 # URL path: /data/local-files/?d=label-studio/raw/...
                                 # v_obj["rel_path"] is relative to /workspace/raw
                                 path_inside_container = v_obj["rel_path"].replace(os.sep, '/')
                                 
                                 # Default to original
                                 final_video_url = f"/data/local-files/?d=label-studio/raw/{path_inside_container}"

                                 # Determine Artifact Directory
                                 base_name = os.path.splitext(fname)[0] 
                                 
                                 # Use json_dir from scanner if available, or deduce
                                 json_dir = v_obj.get("json_dir")
                                 
                                 # Logic: If json_dir looks like .../VideoName, use it.
                                 # Else, create .../raw/VideoName
                                 if json_dir and os.path.basename(json_dir) == base_name:
                                     artifact_dir = json_dir
                                 else:
                                     # parent_dir of video
                                     parent_dir_video = os.path.dirname(v_obj["path"])
                                     artifact_dir = os.path.join(parent_dir_video, base_name)
                                     os.makedirs(artifact_dir, exist_ok=True)

                                 # Generate Audio Proxy (MP3) - Always done for sync
                                 msg_container = st.empty()
                                 msg_container.caption(f"Generating optimized audio for {fname}...")
                                 
                                 audio_filename = f"{base_name}_audio.mp3"
                                 audio_abs_path = os.path.join(artifact_dir, audio_filename)
                                 
                                 generate_audio_proxy(v_obj["path"], audio_abs_path, overwrite=force_reprocess)
                                 
                                 # Audio URL
                                 # Path relative to RAW root
                                 # if artifact_dir is /workspace/raw/VideoName -> rel is VideoName
                                 # Warning: relpath might contain '..' if we are outside. But we assume we are inside raw.
                                 rel_artifact_dir = os.path.relpath(artifact_dir, "/workspace/raw")
                                 audio_rel_path = os.path.join(rel_artifact_dir, audio_filename).replace(os.sep, '/')
                                 
                                 audio_url = f"/data/local-files/?d=label-studio/raw/{audio_rel_path}"

                                 # Generate Video Proxy (Optional)
                                 if use_proxy:
                                     # Define a callback that updates the status text
                                     def proxy_prog_callback(p):
                                         pct = int(p * 100)
                                         status_text.text(f"Processing ({i+1}/{total_items}): {fname}... (Generating Video Proxy: {pct}%)")
                                     
                                     msg_container.caption(f"Generating optimized video proxy for {fname} (this may take a minute)...")
                                     proxy_filename = f"{base_name}_proxy.mp4"
                                     proxy_abs_path = os.path.join(artifact_dir, proxy_filename)
                                     
                                     if generate_video_proxy(v_obj["path"], proxy_abs_path, progress_callback=proxy_prog_callback, overwrite=force_reprocess):
                                         # Update URL to point to proxy
                                         proxy_rel_path = os.path.join(rel_artifact_dir, proxy_filename).replace(os.sep, '/')
                                         final_video_url = f"/data/local-files/?d=label-studio/raw/{proxy_rel_path}"
                                     else:
                                         st.warning(f"Video proxy generation failed for {fname}. Using original.")
                                         # Restore status text
                                         status_text.text(f"Processing ({i+1}/{total_items}): {fname}...")

                                 msg_container.empty()
                                 
                                 task_data = {
                                    "video": final_video_url,
                                    "audio": audio_url,
                                    "meta": v_obj["meta"],
                                    "filename": fname,
                                    "mouse_ids": v_obj["meta"].get("mouse_ids") # Pass all IDs
                                 }
                                 if ls_client.create_task(project_id, task_data):
                                     count += 1
                                     
                             # Update progress
                             progress_bar.progress((i + 1) / total_items)
                        
                        status_text.empty()
                        
                        st.success(f"Uploaded {count} tasks to '{PROJECT_TITLE_MULTI}'")
                    else:
                        st.error("Connection failed.")

    # --- TAB 2: PROCESSED CLIPS ---
    with tab2:
        st.subheader("Processed Clips (Cropped)")
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
                           logger.debug(f"Failed to parse processed video JSON: {e}")
        
        if not found_videos:
            st.info("No processed videos found.")
        else:
            # Selection Table
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
            edited_df = st.data_editor(
                df,
                column_config={"Select": st.column_config.CheckboxColumn("Select", default=False)},
                hide_index=True,
                key="editor_processed"
            )
            
            selected_rows = edited_df[edited_df.Select]
            
            st.divider()

            # Interface Settings (Collapsible)
            with st.expander("⚙️ Label Studio Interface Settings (Screen Size Tuning)"):
                st.caption("If the video is cut off on small screens, reduce the player height here.")
                video_height = st.slider("Video Player Height (px)", min_value=300, max_value=800, value=500, step=50, key="ls_height_slider")
                
                # Generate the config with the selected height
                current_config = LABEL_STUDIO_CONFIG.replace('height="500"', f'height="{video_height}"')
                
                if st.button("Update Interface Layout Only"):
                    ls_client = LabelStudioClient(
                            username=os.getenv("LABEL_STUDIO_USERNAME"),
                            password=os.getenv("LABEL_STUDIO_PASSWORD")
                        )
                    if ls_client.check_connection()[0]:
                        ls_client.get_or_create_project(PROJECT_TITLE, current_config)
                        st.success(f"Interface updated to {video_height}px height! Refresh Label Studio to see changes.")
                    else:
                        st.error("Could not connect to Label Studio.")

            # 3. Push to Label Studio
            st.subheader("Push to Label Studio")
            
            st.info("Authentication is handled automatically via system credentials.")

            # Motion Detection Options
            use_motion_detection = st.checkbox("Run Motion Detection (Skip Inactive Periods)", value=True, help="Analyzes video to find active segments and uploads them as pre-annotations.")
            
            if use_motion_detection:
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    motion_threshold = st.slider("Motion Threshold", 100, 2000, 500, help="Higher = Less sensitive (ignores small movements)")
                with col_m2:
                    min_duration = st.slider("Min Duration (s)", 0.5, 5.0, 1.0, help="Ignore movements shorter than this")

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
                            # Use the config from the slider settings above
                            project_id = ls_client.get_or_create_project(PROJECT_TITLE, current_config)
                            
                            # Ensure Local Storage is configured
                            # For processed clips, we currently map ./workspace/processed -> /label-studio/files
                            ls_client.create_local_storage(project_id, "/label-studio/files")
                            
                            tasks = []
                            selected_filenames = selected_rows["File"].tolist()
                            
                            # Progress bar for motion detection
                            progress_bar = st.progress(0.0)
                            status_text = st.empty()
                            
                            uploaded_count = 0
                            
                            for i, v in enumerate(found_videos):
                                if v["meta"].get("processed_file") in selected_filenames:
                                    status_text.text(f"Processing {v['meta'].get('processed_file')}...")
                                    
                                    # Construct Task
                                    # Mapped path: /workspace/processed -> /label-studio/files
                                    rel_path = v["rel_path"].replace(os.sep, '/')
                                    video_url = f"/data/local-files/?d=label-studio/files/{rel_path}"
                                    
                                    fps = get_video_fps(v["path"])
                                    duration = get_video_duration(v["path"])
                                    if fps == 0: fps = 60.0
                                    
                                    task_data = {
                                        "video": video_url,
                                        "fps": fps,
                                        "meta": v["meta"],
                                        "filename": v["meta"].get("processed_file"),
                                        "mouse_id": v["meta"].get("mouse_id")
                                    }
                                    
                                    # 1. Create Task
                                    task_id = ls_client.create_task(project_id, task_data)
                                    
                                    if task_id:
                                        uploaded_count += 1
                                        
                                        # 2. Run Motion Detection & Upload Annotation
                                        if use_motion_detection:
                                            status_text.text(f"Scanning for motion: {v['meta'].get('processed_file')}...")
                                            try:
                                                motion_scores = detect_motion(v["path"])
                                                segments = generate_segments(motion_scores, threshold=motion_threshold, min_duration=min_duration)
                                                
                                                if segments:
                                                    prediction_payload = LabelStudioClient.format_prediction_result(segments, duration=duration)
                                                    
                                                    annotation = {
                                                        "result": prediction_payload["result"],
                                                        "was_cancelled": False,
                                                        "ground_truth": False
                                                    }
                                                    
                                                    ls_client.create_annotation(task_id, annotation)
                                                    st.caption(f"Found {len(segments)} active segments for {v['meta'].get('mouse_id')}")
                                            except Exception as e:
                                                st.warning(f"Motion detection failed for {v['meta'].get('processed_file')}: {e}")
                                    else:
                                        st.error(f"Failed to create task for {v['meta'].get('processed_file')}")

                                    progress_bar.progress((i + 1) / len(found_videos))
                            
                            if uploaded_count > 0:
                                st.success(f"Successfully imported {uploaded_count} tasks to Project #{project_id}!")
                                
                                # Get public URL for Label Studio (useful for remote access via Tailscale)
                                ls_public_url = os.getenv("LABEL_STUDIO_PUBLIC_URL", "http://localhost:8080").rstrip('/')
                                st.markdown(f"[Open Label Studio]({ls_public_url}/projects/{project_id})")
                            else:
                                st.warning("No tasks generated. Something went wrong with matching selections.")
                                
                        else:
                            st.error(f"Could not connect to Label Studio: {error_msg}")
                            
                    except Exception as e:
                        st.error(f"Upload failed: {e}")
            else:
                st.info("Select videos in the table above to enable upload.")

# --- DATA EXPORT PAGE ---
elif page == "Data Export":
    st.header("Data Synchronization (Export)")
    st.markdown("Export labelled data from Label Studio and convert it to analyzable CSV format.")
    
    # Initialize LS Client
    ls_client = LabelStudioClient()
    connected, error = ls_client.check_connection()
    
    if not connected:
        st.error(f"Could not connect to Label Studio: {error}")
    else:
        st.success("Connected to Label Studio")
        
        try:
             # Just getting list of projects
             response = ls_client.session.get(f"{ls_client.url}/api/projects")
             if response.status_code == 200:
                 projects = response.json().get('results', [])
                 if projects:
                     project_options = {p['id']: f"{p['title']} (ID: {p['id']})" for p in projects}
                     
                     selected_project_id = st.selectbox("Select Project to Export", 
                                                      options=list(project_options.keys()),
                                                      format_func=lambda x: project_options[x])
                     
                     st.info(f"Ready to export data from Project ID: {selected_project_id}")
                     
                     if st.button("Export Data"):
                         with st.spinner("Downloading and processing export..."):
                             try:
                                 # 2. Export JSON
                                 export_data = ls_client.export_snapshot(selected_project_id, export_type='JSON')
                                 
                                 task_count = len(export_data) if export_data else 0
                                 st.info(f"Retrieved {task_count} tasks from Label Studio.")

                                 # Debug: Show what we got
                                 with st.expander("Debug: Raw Export Data (First Task)"):
                                     if export_data and len(export_data) > 0:
                                         st.json(export_data[0])
                                 
                                 # 3. Process to CSV
                                 timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                                 output_filename = f"mouse_behavior_export_{timestamp}.csv"
                                 output_path = os.path.join("/workspace/outputs", output_filename)
                                 
                                 saved_path = process_export_to_csv(export_data, output_path)
                                 
                                 if saved_path:
                                     st.success(f"Export complete!")
                                     st.markdown(f"**Saved to:** `{saved_path}`")
                                     
                                     # Optional: DataFrame Preview
                                     if os.path.exists(saved_path):
                                         df = pd.read_csv(saved_path)
                                         st.dataframe(df.head())
                                 else:
                                     st.warning("Export completed but no labeled data was found to save.")
                                     
                             except Exception as e:
                                 st.error(f"Export failed: {e}")
                                 
                 else:
                     st.warning("No projects found in Label Studio.")
             else:
                 st.error("Failed to list projects.")
                 
        except Exception as e:
            st.error(f"Error accessing projects: {e}")

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
            
            processed_files = []
            for root, _, filenames in os.walk(processed_path):
                for filename in filenames:
                    # Optional: Filter for known types if needed, but for system check seeing everything is good
                    processed_files.append(os.path.relpath(os.path.join(root, filename), processed_path))
            
            if len(processed_files) > 0:
                st.write(f"Found {len(processed_files)} processed items:")
                st.code("\n".join(processed_files))
            else:
                st.info("No processed videos found yet.")
        else:
            st.error("❌ `/workspace/processed` missing")
             
    else:
        st.error(f"Workspace not found at `{workspace_path}`.")

elif page == "Processing (Coming Soon)":
    st.info("This module will handle motion heuristics and analysis.")
