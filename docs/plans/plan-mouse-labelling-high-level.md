# **Project Plan: Mouse Behavior Analysis Pipeline**

**Objective:** streamline the quantification of nasal rubbing incidents in experimental mice by automating video preprocessing and providing an efficient local labelling interface.

## **1\. High-Level Architecture**

Philosophy: Local Compute, Cloud Truth.  
The system relies on Google Drive as the central repository for raw videos and final data. Heavy processing (cropping, rendering, labelling) occurs on the researcher's local machine using a containerized environment to ensure consistency across Windows/Mac/Linux.

### **The Stack**

* **Orchestration:** Docker Compose  
* **Language:** Python 3.9+  
* **Video Processing:** FFmpeg (via ffmpeg-python) & OpenCV  
* **Labelling Interface:** Label Studio (Open Source)  
* **Storage:** Google Drive (via PyDrive2 or Google Drive for Desktop mount)

## **Phase 1: Infrastructure Setup (ENV)**

**Goal:** Create a reproducible environment that any grad student can spin up with one command.

| ID | Task Name | Description | Technical Implementation |
| :---- | :---- | :---- | :---- |
| **ENV-01** | Docker Compose Configuration | Create docker-compose.yml to spin up the Labelling UI and the Python processing container. | Service 1: label-studio (Port 8080\) Service 2: processor (Python \+ FFmpeg) |
| **ENV-02** | Google Drive Access Strategy | Determine how the script accesses the "Mice Recordings" folder. | **Recommended:** Use "Google Drive for Desktop" to mount Drive as a local G: or /Volumes/ drive. This avoids complex API OAuth flows for non-technical users. |
| **ENV-03** | Directory Structure Standardization | Define the local workspace structure to prevent file clutter. | /workspace/raw (input) /workspace/processed (cropped) /workspace/outputs (CSVs) |

> **Implementation Note (Phase 1):**
> Due to Docker on Windows limitations with mounting virtual drives (Google Drive for Desktop), I adopted a **"Staging Area"** workflow.
> *   **Change:** Instead of mounting `G:` directly into Docker, users copy raw files to the local `workspace/raw` folder ("The Inbox").
> *   **Benefit:** This maintains a zero-dependency setup (no local Python/FFmpeg required) while bypassing the mount issue.
> *   **Reference:** See `docs/plans/plan-phase-1-infrastructure.md` for details.

## **Phase 2: Ingestion & Pre-processing (ING)**

**Goal:** Convert single 4-cage videos into individual, ID-tagged mouse videos.

| ID | Task Name | Description | Technical Implementation |
| :---- | :---- | :---- | :---- |
| **ING-01** | Metadata Parsing Logic | Create a mapping function that parses the folder structure provided in "Mice Recordings Explanation" to assign Mouse IDs. | **Input:** Path .../Group 1: Saline-3/Saline-3\_Dec2.M4V **Logic:** Lookup "Group 1" in config. **Output:** {Cage1: 212753, Cage2: 211673...} |
| **ING-02** | ROI Selector Tool | A simple Python GUI to let the user draw 4 bounding boxes on the *first* frame of a video. | cv2.selectROIs (OpenCV). User draws 4 boxes once; coordinates are saved to JSON. |
| **ING-03** | FFmpeg Batch Cropping | Cut the source video into 4 separate files based on ROI coordinates. | ffmpeg \-i input.mp4 \-filter:v "crop=w:h:x:y" mouse\_{ID}.mp4 |
| **ING-04** | Metadata Injection | Attach the Mouse ID, Date, and Treatment Group to the filename or a companion JSON sidecar. | Filename format: MouseID\_Date\_Treatment\_Condition.mp4 |

## **Phase 3: Motion Heuristics (HEU)**

**Goal:** Identify periods of inactivity to allow researchers to skip empty footage.

| ID | Task Name | Description | Technical Implementation |
| :---- | :---- | :---- | :---- |
| **HEU-01** | Frame Difference Calculator | Calculate pixel intensity changes between consecutive frames to detect movement. | Convert to grayscale $\\rightarrow$ GaussianBlur $\\rightarrow$ absdiff $\\rightarrow$ Threshold. |
| **HEU-02** | Activity Thresholding | Define "Active" vs. "Sleeping" segments. | If motion\_score \< 500 for \> 5 seconds, mark as Inactive. |
| **HEU-03** | Timeline Generation | Generate a format Label Studio can read to visualize activity on the timeline. | Export a JSON time-series file compatible with Label Studio's "Audio/Video Regions" format. |

## **Phase 4: Labelling Interface (LAB)**

**Goal:** Configure Label Studio to allow rapid "start/stop" annotation of rubbing events.

| ID | Task Name | Description | Technical Implementation |
| :---- | :---- | :---- | :---- |
| **LAB-01** | Interface Configuration | XML configuration for Label Studio defining the classes and layout. | \<View\>\<Video name="video" ... /\>\<Labels\>\<Label value="Rubbing" background="red"/\>\<Label value="Eating" background="green"/\>\</Labels\>\</View\> |
| **LAB-02** | Task Import Script | Python script to push the cropped videos and their metadata into Label Studio via API. | POST /api/projects/{id}/import with the JSON payload of video paths. |
| **LAB-03** | User Workflow Documentation | A 1-page PDF guide for students on how to use hotkeys to mark regions. | e.g., "Press '1' to start Rubbing label, Press '1' again to end." |

## **Phase 5: Data Synchronization (SYN)**

**Goal:** Ensure valuable labelled data returns to the shared Drive.

| ID | Task Name | Description | Technical Implementation |
| :---- | :---- | :---- | :---- |
| **SYN-01** | Export Formatting | Convert Label Studio JSON export into a flat CSV tailored for analysis (Duration, Frequency). | Columns: MouseID, Date, Rub\_Start\_Time, Rub\_End\_Time, Duration\_Seconds |
| **SYN-02** | Re-upload Logic | Script to copy the CSV back to the specific "Group" folder in Google Drive. | Copy file from local ./outputs to G:/My Drive/Mice Recordings/... |

## **Implementation Roadmap (Estimate: 2 Weeks)**

### **Week 1: The Core Pipeline**

1. **Days 1-2:** Build **ING-02** and **ING-03** (The ROI cropper). This is the highest value immediate tool.  
2. **Days 3-4:** Build **ENV-01** (Docker) and **LAB-01** (Label Studio Config). Verify you can load a cropped video and label it.  
3. **Day 5:** Write **ING-01** (Metadata Parser) to automate the naming convention.

### **Week 2: Optimization & UI**

1. **Days 6-7:** Implement **HEU-01** (Motion Detection). Even a crude implementation helps.  
2. **Day 8:** Connect the pieces. Script the flow: Select Video \-\> Crop \-\> Push to Label Studio.  
3. **Days 9-10:** Documentation and User Testing with one researcher.