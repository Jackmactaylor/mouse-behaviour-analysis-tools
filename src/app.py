import streamlit as st
import subprocess
import os
import sys
import cv2

st.set_page_config(page_title="Mouse Behavior Analysis", page_icon="🐭")

st.title("🐭 Mouse Behavior Analysis Pipeline")

st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["System Check", "Ingestion (Coming Soon)", "Processing (Coming Soon)"])

if page == "System Check":
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
            st.info("Drag your video files here to start processing.")
            
            files = os.listdir(raw_path)
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

elif page == "Ingestion (Coming Soon)":
    st.info("This module will handle video ingestion and cropping.")

elif page == "Processing (Coming Soon)":
    st.info("This module will handle motion heuristics and analysis.")
