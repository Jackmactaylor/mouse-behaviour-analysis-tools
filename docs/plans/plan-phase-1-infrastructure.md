---
title: Phase 1: Infrastructure Setup
version: 1.0
date_created: 2025-12-08
last_updated: 2025-12-08
---

## Implementation Plan: Phase 1 - Infrastructure Setup (ENV)

This phase focuses on establishing the reproducible environment required for the mouse behavior analysis pipeline. It involves setting up Docker Compose to orchestrate the Label Studio interface and the Python processing backend, standardizing the local directory structure, and defining the strategy for accessing Google Drive data.

## Architecture and design

**Philosophy:** Local Compute, Cloud Truth.
**Core Components:**
1.  **Docker Compose:** The central orchestration tool.
    *   **Service 1: `label-studio`**: The official Label Studio image for data annotation.
    *   **Service 2: `processor`**: A custom Python 3.9+ image containing `ffmpeg`, `opencv`, and project scripts.
2.  **Storage Strategy:**
    *   **Google Drive:** Accessed via "Google Drive for Desktop" (mounted as a local drive, e.g., `G:`).
    *   **Local Workspace:** A structured directory on the host machine for intermediate processing, bind-mounted into containers.

**Design Decisions:**
*   **Bind Mounts:** We will use bind mounts for the workspace to ensure easy access to files from the host OS for debugging and file management.
*   **Environment Variables:** Configuration (paths, ports) will be managed via a `.env` file.
*   **Label Studio Local Files:** We must enable `LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true` to allow Label Studio to access the processed videos directly from the disk.

## Supporting Documentation

*   `docs/plans/plan-mouse-labelling-high-level.md` (High-level roadmap)
*   `docs/agent-guidelines.md` (Project constraints and philosophy)

## Tasks

- [x] **ENV-01: Docker Configuration**
    - [x] Create `Dockerfile` for the `processor` service (Python 3.9, FFmpeg, OpenCV, Streamlit).
    - [x] Create `docker-compose.yml` defining `label-studio` and `processor` services.
        - [x] Expose Port 8501 for Streamlit.
    - [x] Configure volume mappings for persistence (Label Studio data) and workspace access.
    - [x] Set up `.env` file for configuration (including `GOOGLE_DRIVE_PATH`).

- [x] **ENV-02: Directory Structure Standardization**
    - [x] Create a setup script (e.g., `setup_workspace.py`) to generate the required folder structure:
        - `/workspace/raw` (Input cache)
        - `/workspace/processed` (Cropped videos)
        - `/workspace/outputs` (CSVs/JSONs)
    - [x] Ensure `.gitignore` properly excludes these data folders.

- [x] **ENV-03: Google Drive Access Documentation**
    - [x] Document the requirement for "Google Drive for Desktop".
    - [x] Add instructions to `README.md` on how to configure the drive letter in `.env`.

- [x] **ENV-04: Verification UI (Streamlit)**
    - [x] Create `app.py` (Streamlit entry point) in the `processor` container.
    - [x] Implement a "System Check" page to verify:
        - FFmpeg installation (`ffmpeg -version`).
        - OpenCV installation (`import cv2`).
        - Google Drive access (check if configured path exists).
        - Local file serving is active in Label Studio (check env var).

## Decisions

1.  **Label Studio Database:** SQLite (default) will be used for simplicity.
2.  **Processor Interaction:** A minimal Streamlit UI will be provided for non-technical users.
3.  **OS Specifics:** Google Drive path will be configurable via `.env` to handle different drive letters (e.g., `G:`, `D:`).
4.  **Data Ingestion Strategy (Updated):** Due to Docker on Windows limitations with mounting virtual drives (Google Drive for Desktop), we are adopting a "Staging Area" workflow.
    *   **Limitation:** Docker cannot reliably mount the `G:` virtual drive.
    *   **Solution:** Users will copy raw video files from `G:` to the local `workspace/raw` folder ("The Inbox").
    *   **Benefit:** Maintains zero-dependency setup (no local Python/FFmpeg required) while bypassing the mount issue.

## Success criteria

1.  User can run `docker-compose up` and access:
    -   Label Studio at `http://localhost:8080`.
    -   Processor UI at `http://localhost:8501`.
2.  The `processor` container has `ffmpeg`, `cv2`, and `streamlit` installed.
3.  The Streamlit UI successfully reports "All Systems Go" when checking dependencies and paths.
4.  Label Studio can import a dummy video file from the local `processed` directory.

## Test plan

1.  **Build Test:** Run `docker-compose build` to ensure the Python image builds correctly.
2.  **Run Test:** Run `docker-compose up -d` and check container status.
3.  **UI Test:** Open `http://localhost:8501` and run the system check.
4.  **Integration Test:**
    *   Place a dummy video in `workspace/processed`.
    *   Verify it is visible inside the `label-studio` container.
