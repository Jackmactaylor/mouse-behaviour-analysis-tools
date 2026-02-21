# Technical Blurb Notes for Research Paper

## Overview
Local-first video analysis pipeline for quantifying mouse allergy responses (nasal rubbing behavior) in experimental settings. Designed for non-technical researchers to annotate multi-cage video recordings with precise temporal data.

---

## Problem Statement (Technical Context)
- **Input:** Long-duration videos (hours) containing 4 mouse cages recorded simultaneously
- **Manual workflow issues:**
  - Sequential review required (watch mouse 1, rewind, watch mouse 2, etc.)
  - Manual timestamp logging prone to transcription errors
  - Mouse ID mapping stored separately from annotations
  - Difficult to capture precise event durations
  - Workflow scales linearly: 4 mice = 4× time investment

---

## Architecture & Design Philosophy

### Core Principle: "Local Compute, Local Truth"
- **No external databases:** Filesystem acts as the database (workspace directory structure)
- **Docker-based:** Entire stack runs in containers for reproducibility across Windows/Mac/Linux lab environments
- **Local processing:** All video rendering and annotation occurs on researcher's machine (no cloud latency/costs)
- **Data persistence:** Raw data and CSV outputs stored in Google Drive for lab-wide access

### System Architecture
```
┌─────────────────────────────────────────────────────┐
│  Researcher's Computer (Docker Desktop)             │
│                                                      │
│  ┌──────────────────┐      ┌──────────────────┐   │
│  │   Streamlit      │◄────►│  Label Studio    │   │
│  │   Dashboard      │ API  │   (HeartexLabs)  │   │
│  │   (Port 8501)    │      │   (Port 8080)    │   │
│  └────────┬─────────┘      └────────┬─────────┘   │
│           │                          │              │
│           ▼                          ▼              │
│  ┌────────────────────────────────────────────┐   │
│  │      Shared Volume: /workspace             │   │
│  │  - raw/           (input videos)           │   │
│  │  - processed/     (cropped clips)          │   │
│  │  - outputs/       (CSV exports)            │   │
│  └────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Containerization & Orchestration
- **Docker Compose:** Multi-container orchestration
  - `label-studio` service: HeartexLabs Label Studio v1.12.1
  - `processor` service: Custom Python application

### Backend & Processing
- **Python 3.9+** with core libraries:
  - `ffmpeg-python`: Wrapper for FFmpeg video manipulation
  - `opencv-python`: Computer vision operations (frame extraction, drawing ROIs)
  - `streamlit`: Web-based dashboard interface
  - `requests`: Label Studio API integration

### Video Processing Pipeline
- **FFmpeg:** Hardware-accelerated video transcoding
  - H.264 encoding with x264 codec
  - Audio extraction for waveform visualization
  - ROI-based cropping with parallel processing
  - Web-optimized proxy generation (720p, CRF 26)

### Annotation Interface
- **Label Studio:** Open-source data labeling platform
  - Custom XML configuration for timeline segmentation
  - Dual-project system:
    - Project 1: Multi-mouse (4 mice, original video)
    - Project 2: Single-mouse (cropped clips)
  - REST API for programmatic task import/export

---

## Key Technical Features

### 1. Fixed ROI Workflow (Alternative to Object Detection)
- Researcher draws bounding boxes on first frame
- Same ROIs applied to entire video duration
- **Rationale:** Mice in fixed cages don't require YOLO/R-CNN tracking
- **Performance:** ~4x faster than object detection approaches
- Parallel processing: 4 crops generated simultaneously using ThreadPoolExecutor

### 2. Automated Metadata Parsing
- Directory structure encodes experimental metadata:
  ```
  workspace/raw/Dec2/Group5_Control/212753_Dec2_Control.mp4
  ```
- Parser extracts: Date, Group, Treatment from path hierarchy
- Mouse IDs mapped via `mouse_map.csv` lookup table
- JSON sidecar created: `212753_Dec2_Control.mp4.meta.json`

### 3. Timeline Segmentation for Duration Capture
- Uses Label Studio's `<TimelineLabels>` component
- Researchers click-and-drag on audio waveform to mark behavior events
- Captures: `start_time`, `end_time`, `behavior_type`, `mouse_id`
- Precision: Frame-accurate (based on video FPS)

### 4. Multi-Mouse Annotation Workflow
- **Innovation:** Label all 4 mice in single pass of video
- Label naming convention: `Rubbing (M1)`, `Rubbing (M2)`, etc.
- Reduces annotation time from 4× to 1× video duration
- Backend maps `M1`/`M2`/`M3`/`M4` to specific mouse IDs during CSV export

### 5. Data Export & Analysis Pipeline
- Label Studio exports JSON annotations via REST API
- Custom `data_exporter.py` transforms to analysis-ready CSV:
  - Resolves `M1` → actual mouse ID (e.g., "212753")
  - Calculates event duration (end - start)
  - Adds metadata columns (Treatment, Date, Group)
- Output format compatible with R/Python statistical analysis

---

## Data Flow & Workflow

### Stage 1: Ingestion (Registration)
1. Videos placed in `workspace/raw/` directory
2. Streamlit dashboard parses directory path → suggests metadata
3. Researcher verifies/corrects mouse IDs and treatment groups
4. System creates `.meta.json` sidecar (registration proof)

### Stage 2A: Multi-Mouse Labeling (Primary Workflow)
1. Dashboard scans for registered videos (those with `.meta.json`)
2. Upload to Label Studio "Multi-Mouse" project via API
3. Researcher annotates using 4 label sets: `M1_Rubbing`, `M2_Rubbing`, etc.
4. Direct timeline segmentation on original 4-cage video

### Stage 2B: ROI Processing (Optional Legacy Workflow)
1. Load registered video in ROI Selector component
2. Draw 4 bounding boxes (one per cage)
3. FFmpeg crops video into 4 individual files:
   ```
   workspace/processed/Dec2/Group5_Control/212753_Dec2_Control_crop.mp4
   ```
4. Upload cropped videos to "Single-Mouse" Label Studio project

### Stage 3: Annotation
- Label Studio web interface (port 8080)
- Video player with synchronized audio waveform
- Hotkeys: `1` = Rubbing, `2` = Grooming, `3` = Eating, `Space` = Play/Pause
- Annotations saved to Label Studio's internal SQLite database

### Stage 4: Export
1. Dashboard calls Label Studio API: `GET /api/projects/{id}/export`
2. JSON response contains all annotations with timestamps
3. `process_export_to_csv()` function:
   - Parses annotation format (multi-mouse vs single-mouse)
   - Maps positional mouse IDs (`M1`) to actual IDs from metadata
   - Flattens nested JSON → tabular CSV
4. Output: `mouse_behavior_export_YYYY-MM-DD_HH-MM-SS.csv`

---

## Technical Innovations & Optimizations

### 1. Parallel Video Processing
- ThreadPoolExecutor processes 4 ROI crops simultaneously
- Shared progress callback via thread-safe dictionary
- Streamlit context propagation to worker threads
- Typical speedup: 4× vs sequential processing

### 2. Web-Optimized Proxy Generation
- Original videos often large (>1GB, 4K resolution)
- System generates lightweight proxies:
  - Downscaled to 720p
  - H.264 with CRF 26 (20-30% original size)
  - Separate MP3 audio track for waveform rendering
  - FastStart flag for progressive loading
- Trade-off: Annotation speed vs researcher convenience (full resolution not required)

### 3. Filesystem-as-Database Pattern
- No SQL/NoSQL setup required (barrier for non-technical users)
- Directory hierarchy = data schema:
  ```
  workspace/
    raw/              # Inbox (unprocessed)
    processed/        # Cropped videos
    outputs/          # CSV exports
    mouse_map.csv     # Treatment groups lookup
  ```
- Sidecar JSON files provide metadata without centralized DB
- Git-friendly (JSON diffs trackable)

### 4. API-Driven Label Studio Integration
- Direct SQLite access for API token retrieval (avoids manual config)
- Automatic project creation/update via REST API
- Task import with embedded metadata (mouse IDs travel with video)
- Export pulls latest annotations without UI interaction

### 5. Cross-Platform Filesystem Handling
- Uses `pathlib` and `os.path.join()` for Windows/Unix compatibility
- Volume mounts in docker-compose handle Windows path translation
- URI encoding for spaces in filenames (Docker → Label Studio)

---

## Performance Characteristics

### Video Processing Benchmarks (Typical Lab Hardware)
- **Input:** 1920×1080, 30fps, 2-hour video (~8GB)
- **ROI Cropping:** ~15-20 minutes (4 crops in parallel)
- **Proxy Generation:** ~10 minutes per video (720p transcode)
- **Annotation Speed:** Real-time (1 hour video = 1 hour annotation time)

### Scalability Considerations
- **Current scope:** Designed for single-user desktop operation
- **Concurrent users:** Label Studio supports multi-user, but Docker Compose deployment is single-instance
- **Storage:** ~50GB for 10 full-resolution videos + crops + proxies
- **Remote access:** Tailscale VPN integration for lab-wide access

---

## Security & Access Control

### Authentication
- Label Studio: Username/password (environment variables)
- API token stored in SQLite, auto-retrieved by pipeline
- CSRF protection via trusted origins list

### Network Isolation
- Services communicate via Docker internal network (`label-studio:8080`)
- External access only via localhost or Tailscale VPN
- No public internet exposure

---

## Limitations & Design Constraints

1. **Fixed ROI Assumption:** Requires mice to remain in defined cage areas (not suitable for open-field tests)
2. **Manual First-Pass:** Researcher must define ROIs (no automatic cage detection)
3. **Single-Instance:** Not cloud-scalable without significant rearchitecture
4. **Windows Docker:** Performance considerations for file I/O on Windows host volumes
5. **Video Format:** Assumes standard codecs (H.264/H.265); exotic formats may require pre-conversion

---

## Future Extensibility

### Potential Additions (Not Yet Implemented)
- Motion heuristics: Pre-scan videos to skip inactive periods (sleeping mice)
- Automatic ROI detection via computer vision (Hough transforms for cage grids)
- Integration with statistical analysis (R/Python notebooks)
- Cloud deployment option (Kubernetes, S3 storage)
- Active learning: Model training on labeled data for suggestions

---

## Deployment & Reproducibility

### System Requirements
- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- 8GB+ RAM recommended
- 50GB+ free disk space per experiment

### Single-Command Startup
```bash
docker-compose up -d
```
- Automatically pulls pre-built Label Studio image
- Builds custom processor container from Dockerfile
- Mounts workspace volumes
- Initializes Label Studio database if not present

### Environment Variables (docker-compose.yml)
- `LABEL_STUDIO_USERNAME` / `_PASSWORD`: Admin credentials
- `CSRF_TRUSTED_ORIGINS`: Whitelist for remote access
- `LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED`: Permits Docker volume access

---

## Code Quality & Maintainability

### Architecture Patterns
- **Separation of Concerns:** Utilities (`utils/`) vs UI (`app.py`, `components/`)
- **Type Hints:** All functions use Python type annotations
- **Error Handling:** Graceful failures with user-readable messages
- **Logging:** Standardized logging via `logging.basicConfig()`

### Testing Infrastructure
- `tests/` directory with validation scripts:
  - `test_auth.py`: Verify Label Studio authentication
  - `test_metadata.py`: Validate metadata parsing logic
  - `inspect_ls_tasks.py`: Debug Label Studio task structure

---

## Summary Statistics (Current Implementation)

- **Total codebase:** ~2,000 lines Python
- **Docker images:** 2 containers
- **API endpoints used:** 6 (Label Studio REST API)
- **Supported video formats:** MP4, MOV, AVI (FFmpeg-compatible)
- **Annotation types:** 3 behaviors (Rubbing, Grooming, Eating) × 4 mice
- **Export formats:** CSV, JSON

---

## References to Include in Paper

### Software Dependencies
- Label Studio: Tkachenko et al., "Label Studio: Data Labeling Software" (Open-source, Apache 2.0)
- FFmpeg: https://ffmpeg.org
- Streamlit: https://streamlit.io
- Docker: Container runtime (https://docker.com)

### Standards & Formats
- Label Studio JSON schema: https://labelstud.io/guide/export.html
- H.264/AVC video codec: ITU-T H.264 standard

