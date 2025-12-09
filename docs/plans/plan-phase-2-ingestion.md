---
title: Phase 2: Ingestion & Pre-processing
version: 1.0
date_created: 2025-12-08
last_updated: 2025-12-08
---

## Implementation Plan: Phase 2 - Ingestion & Pre-processing (ING)

This phase focuses on building the core "Ingestion Engine" of the pipeline. It enables users to select raw videos from the Staging Area (`workspace/raw`), define Regions of Interest (ROIs) for individual mice, and batch-process them into standardized, cropped video files ready for labelling.

## Architecture and design

**Philosophy:** "Staging Area" Workflow.
**Core Components:**
1.  **Streamlit UI (Frontend):**
    *   **Inbox Browser:** Lists files in `workspace/raw`.
    *   **ROI Selector:** A web-based canvas (using `streamlit-drawable-canvas`) to draw 4 bounding boxes on the first frame of a selected video.
    *   **Metadata Form:** Auto-populated fields based on file path, with user override capabilities.
2.  **Processing Engine (Backend):**
    *   **Metadata Parser:** Extracts Mouse ID, Treatment, and Date from the directory structure.
    *   **FFmpeg Wrapper:** Uses `ffmpeg-python` to perform precise cropping without re-encoding (if possible) or high-quality re-encoding.

**Design Decisions:**
*   **Web-Based ROI:** Since the processor runs in Docker, we cannot use `cv2.selectROIs` (which requires a local window system). We will use `streamlit-drawable-canvas` to draw boxes on a frame extracted by OpenCV.
*   **Metadata Source:** We assume the user copies the *folder structure* from Drive to `workspace/raw`. The parser will read the relative path (e.g., `Group 1/Saline/video.mp4`) to infer metadata.
*   **Output Naming:** Strict adherence to `MouseID_Date_Treatment_Condition.mp4` to ensure downstream tools (Label Studio) can sort/filter easily.

## Supporting Documentation

*   `docs/plans/plan-mouse-labelling-high-level.md` (Phase 2 goals)
*   `docs/agent-guidelines.md` (Constraints: Staging Area, Fixed ROI)

## Tasks

- [ ] **ING-01: Metadata Parsing Module**
    - [ ] Create `src/utils/metadata.py`.
    - [ ] Implement logic to parse file paths relative to `workspace/raw`.
    - [ ] **Logic:** Map folder names to experimental groups (e.g., "Group 1" -> Treatment: Saline).
    - [ ] **Test:** Unit test with various sample path strings.

- [ ] **ING-02: Streamlit ROI Selector**
    - [ ] Add `streamlit-drawable-canvas` to `docker/processor/requirements.txt` and rebuild.
    - [ ] Create `src/components/roi_selector.py`.
    - [ ] Implement functionality:
        - [ ] Extract 1st frame of selected video using `cv2`.
        - [ ] Display frame in canvas.
        - [ ] Allow drawing of exactly 4 rectangles (enforce count if possible, or validate on submit).
        - [ ] Return coordinates scaled to original video resolution.

- [ ] **ING-03: FFmpeg Cropping Engine**
    - [ ] Create `src/utils/video_processor.py`.
    - [ ] Implement `crop_video(input_path, rois, output_dir, metadata)` function.
    - [ ] Use `ffmpeg-python` to generate 4 separate output files in parallel or sequence.
    - [ ] Apply naming convention: `{MouseID}_{Date}_{Treatment}.mp4`.

- [ ] **ING-04: UI Integration & "The Big Red Button"**
    - [ ] Update `src/app.py` to include the "Ingestion" page.
    - [ ] Workflow:
        1.  Select Video from Dropdown (scanned from `raw`).
        2.  Show parsed metadata (allow edit).
        3.  Draw ROIs.
        4.  Click "Process".
        5.  Show progress bar.
        6.  Display success message with paths to generated files in `processed`.

## Open questions & clarifications

1.  **Metadata Mapping:** Do we need a `config.json` to map "Group 1" to specific Mouse IDs, or is the Mouse ID in the filename/folder? *Assumption: We will implement a flexible parser that looks for patterns but allows manual override in the UI.*
2.  **Re-encoding:** Should we re-encode to a web-friendly format (H.264/MP4) during cropping to ensure Label Studio compatibility? *Decision: Yes, force re-encode to H.264 to avoid browser playback issues.*

## Success criteria

1.  User can see a list of videos present in `workspace/raw`.
2.  User can draw 4 boxes on a video frame in the browser.
3.  Clicking "Process" generates 4 valid `.mp4` files in `workspace/processed`.
4.  Generated filenames match the required convention.

## Test plan

1.  **Unit Test:** `test_metadata_parser.py` checks if `raw/Group1/Cage1/video.mp4` parses correctly.
2.  **Manual UI Test:**
    *   Place video in `workspace/raw`.
    *   Open Streamlit.
    *   Draw boxes.
    *   Verify outputs in `workspace/processed` play in VLC/Media Player.
