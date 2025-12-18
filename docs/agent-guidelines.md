# **Agent Guidelines & Context**

Role: You are an intelligent coding assistant helping to build a local-first video analysis pipeline for biology researchers.  
Primary Constraint: This software is for non-technical users (researchers) running on standard lab computers. Robustness and simplicity \> complex architecture.

## **Key References**

* **Project Overview:** README.md (Root)  
* **Implementation Plan:** docs/plans/plan-mouse-behaviour-analysis-pipeline.md  
  * *Consult this plan for specific Task IDs (e.g., ING-02, HEU-01) before generating code.*

## **Core Philosophy: "Local Compute, Local Truth"**

1. **The Filesystem is the Database:** The directory structure in the `workspace` folder acts as our database. We do not use SQL/NoSQL databases.  
2. **Docker is the Runtime:** Everything must run via docker-compose. Assume the user has Docker Desktop and nothing else.

## **Tech Stack Standards**

* **Language:** Python 3.9+  
* **Video Processing:** ffmpeg-python (wrapper for FFmpeg) and opencv-python (for simple CV tasks/drawing).  
* **GUI/Interface:** Label Studio (for labelling) or simple Streamlit/Tkinter (for lightweight local tools).  
* **Environment:** Docker Compose.

## **Critical Constraints**

1. **The "Fixed ROI" Rule:** Do not implement object detection (YOLO/R-CNN) for mouse tracking. Use fixed bounding boxes drawn by the user on the first frame.  
2. **File Naming:** Strict adherence to the mapping logic in the plan is required. Metadata (Mouse ID, Treatment) must be parsed from the folder path, not guessed.  
3. **OS Agnostic:** The code must run on Windows (common in labs) and Mac/Linux. Avoid OS-specific file paths; use os.path.join or pathlib.
4. **Staging Area Workflow:** Due to Docker/Windows limitations, we use a "Staging Area". Users copy files to `workspace/raw`. The pipeline reads from there.

## **Coding Style**

* **Docstrings:** Required for all functions, specifically explaining input/output shapes for video arrays.  
* **Type Hinting:** Mandatory.  
* **Error Handling:** Fail gracefully with user-readable error messages (e.g., "Could not find video file" instead of a stack trace).

## **Common Tasks & Snippets**

* **Data Access:** Do NOT assume direct access to host mounts (like G:/) inside Docker. Use the **Staging Area** pattern: inputs are found in `/workspace/raw` and outputs go to `/workspace/processed`.
* **Cropping:** Always generate crops relative to the original video resolution.