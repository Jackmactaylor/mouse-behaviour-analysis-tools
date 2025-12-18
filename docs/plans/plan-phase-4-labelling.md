---
title: Phase 4: Labelling Interface
version: 1.0
date_created: 2025-12-14
last_updated: 2025-12-14
---

## Implementation Plan: Phase 4 - Labelling Interface (LAB)

This phase focuses on connecting the video processing pipeline to Label Studio. It involves configuring the annotation interface and building the "bridge" that automatically pushes processed videos into Label Studio as tasks, enabling a seamless workflow for researchers.

## Architecture and design

**Philosophy:** "Seamless Handoff".
**Core Components:**
1.  **Label Studio (Service):** Already running via Docker. We will leverage its API and Local File Serving capabilities.
2.  **API Client (Python):** A lightweight wrapper around `requests` to interact with Label Studio's REST API.
3.  **Streamlit Integration:** A new UI section in `app.py` to trigger the upload of processed files.

**Design Decisions:**
*   **Local File Serving:** We are using `LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true`. This means we do *not* upload the actual video files via the API. Instead, we upload a JSON task that points to the file path.
    *   *Path Mapping:* A file at `/workspace/processed/video.mp4` (in Processor) is mounted to `/label-studio/files/video.mp4` (in Label Studio).
    *   *URL Construction:* The API payload must use the URL format: `/data/local-files/?d=video.mp4`.
*   **Project Management:** The script will check if a project named "Mouse Behavior Analysis" exists. If not, it will create it with the standard XML configuration.
*   **Authentication:** We use **Programmatic Session Login**. The client logs in via `POST /user/login/` using credentials (`LABEL_STUDIO_USERNAME`/`PASSWORD`) injected via Docker environment variables, maintaining a session with CSRF tokens. This bypasses the need for manual API tokens or legacy auth flags.

## Supporting Documentation

*   `docs/plans/plan-mouse-labelling-high-level.md`
*   Label Studio API Documentation: https://labelstud.io/api/

## Tasks

- [x] **LAB-01: Label Studio Client Module**
    - [x] Create `src/utils/label_studio.py`.
    - [x] Implement `LabelStudioClient` class using `requests.Session`.
    - [x] Methods: `login()`, `check_connection()`, `get_or_create_project(title, label_config)`, `import_tasks(project_id, tasks)`.
    - [x] **Constraint:** Must handle connection errors gracefully and manage CSRF tokens for session auth.

- [x] **LAB-02: Interface Configuration (XML)**
    - [x] Define the standard XML config for the project.
    - [x] **Config:**
        ```xml
        <View>
          <Video name="video" value="$video" />
          <VideoRectangles name="box" toName="video" />
          <Labels name="label" toName="video">
            <Label value="Rubbing" background="red" hotkey="1"/>
            <Label value="Grooming" background="blue" hotkey="2"/>
            <Label value="Eating" background="green" hotkey="3"/>
          </Labels>
        </View>
        ```
    - [x] Store this as a constant or file in `src/components/`.

- [x] **LAB-03: Streamlit Integration**
    - [x] Update `src/app.py` to include a "Labelling" section (or append to the Processing success state).
    - [x] Remove manual API Token input; instantiate client using `LABEL_STUDIO_USERNAME`/`PASSWORD` env vars.
    - [x] Add "Push to Label Studio" button.
    - [x] **Logic:**
        1.  Iterate through `st.session_state.processed_files`.
        2.  Construct task payload: `{"video": "/data/local-files/?d=<relative_path>", "meta": {...}}`.
        3.  Call `client.import_tasks()`.
        4.  Show success message with a link to the Label Studio project.

- [x] **LAB-04: Documentation**
    - [x] Update `README.md` to reflect automated authentication (no manual token needed).
    - [x] Create a simple "Labelling Guide" PDF/Markdown for students (hotkeys, workflow).

## Open questions & clarifications

1.  **Authentication:** How do we authenticate without manual tokens?
    *   *Answer:* We implemented a session-based login flow (`src/utils/label_studio.py`) that uses the system credentials to programmatically log in and acquire a session cookie.
2.  **Syncing:** What if a file is re-processed?
    *   *Answer:* Label Studio allows importing duplicate data. We will not implement complex deduplication logic yet. Users should manage this manually.

## Success criteria

1.  System automatically authenticates with Label Studio using environment credentials (no user input required).
2.  Clicking "Push to Label Studio" successfully creates a project (if missing) and imports tasks.
3.  User can open Label Studio (`localhost:8080`), see the new tasks, and play the video.
4.  The video player in Label Studio works (proving the Local File Serving path is correct).

## Test plan

1.  **Connection Test:** Verify `src/utils/label_studio.py` can ping the API.
2.  **Import Test:** Manually run a script to push one dummy task and verify it appears in the UI.
3.  **Playback Test:** Open the task in Label Studio and ensure the video loads (no 404 errors).
