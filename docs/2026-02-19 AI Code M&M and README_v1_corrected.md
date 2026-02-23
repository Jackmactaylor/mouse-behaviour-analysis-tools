­Manuscript Material and Methods section

AI-assisted behavioural analysis of nasal rubbing in mice

Video acquisition
Mice were videorecorded in their home cages for 30 minutes following each exposure unless otherwise indicated. Three cages (4 mice per cage) were placed in a biological safety cabinet with open lids, and recording was performed using a fixed smartphone camera mounted on the cabinet glass. Cage positions were rotated between experiments to avoid positional bias. Videos were collected in M4V format (Apple QuickTime) and totaled approximately [X] hours of footage.
<!-- JACK NOTE: "Three cages (4 mice per cage)" — The tool treats the recording as 4 cage positions
     with 1 mouse per cage (M1–M4 labels, 4 ROI boxes, mouse_map.csv has 4 cages per group).
     Wil/Lubnaa should confirm the physical setup and reconcile the wording here. -->

Behavioural event selection and annotation
To enable objective and blinded behavioural quantification, we developed a containerized, local-first video analysis and annotation tool to identify candidate nasal rubbing events. Nasal rubbing was operationally defined as lifting of the forepaws toward the nose region, a movement associated with nasal irritation but also observed during grooming or feeding. The tool reduced video complexity by isolating mouse-specific regions of interest and generating cropped clips for annotation. All candidate events were manually reviewed and classified by a blinded researcher to distinguish nasal rubbing from grooming, feeding, or unrelated movements.

Software architecture and deployment
The system was implemented as a reproducible two-service Docker deployment consisting of (i) a custom processing service for video ingestion, preprocessing, and export, and (ii) Label Studio (v1.12.1) as the annotation interface. The processor automatically registered videos, embedded experimental metadata, generated annotation tasks via the Label Studio REST API, and exported structured mouse-level behavioural datasets.

Video preprocessing and performance optimization
Because mice were recorded in fixed cage positions, regions of interest were defined once and applied across videos to generate per-mouse clips using FFmpeg. To improve annotation efficiency, lightweight proxy videos (downscaled to 720p, H.264 at CRF 26 with faststart flag) and separate audio proxies (MP3, mono, 44100 Hz, 64 kbps) were generated for responsive playback and waveform rendering within Label Studio. Optional motion-based filtering was implemented to flag active segments but was used only as a supplementary aid due to high baseline activity levels.

Annotation workflows and dataset generation
Both multi-mouse and single-mouse annotation configurations were supported to maximize annotation efficiency and dataset flexibility. Metadata, including mouse identity and treatment group, were embedded at import and preserved during export. This pipeline enabled efficient, blinded identification and quantification of nasal rubbing events and produced structured datasets suitable for downstream behavioural analysis and future machine learning applications.

Code availability
The video analysis and annotation pipeline developed for this study is available as an open-source, containerized software package. The tool enables reproducible preprocessing, annotation, and export of structured behavioral datasets from multi-mouse video recordings. The complete source code, deployment configuration, annotation schemas, and documentation are available at:
GitHub: https://github.com/[ORG_OR_USERNAME]/mouse-behaviour-analysis-tools

---

GitHub Repository README

# Mouse Behavior Annotation Tool

Local-first, containerised video annotation platform for quantifying clinically relevant behavioural patterns in mice, with structured dataset export for downstream analysis and machine learning.

## Overview

This tool was developed to support behavioural quantification of nasal rubbing events in mice exposed to inhaled allergens. The platform accelerates manual behavioural annotation while producing structured, reusable datasets suitable for downstream statistical analysis and future machine learning model development.

The system is designed for reproducibility, accessibility, and extensibility. It runs entirely locally using Docker containers, requires no Python installation on the host system, and provides a browser-based interface for efficient annotation.

Primary objectives:
1. Accelerate manual annotation of clinically relevant behaviour
2. Generate structured, mouse-level datasets suitable for future automated behavioural classification

## Scientific Context

Manual behavioural annotation of laboratory mice from continuous video recordings is time-consuming and prone to inefficiencies due to:
- Large video file sizes
- Multi-animal recordings requiring sequential review per mouse
- Web playback latency when loading high-resolution source videos
- Lack of structured export formats linking annotations to experimental metadata

This tool addresses these challenges by:
- Isolating mouse-specific video regions via fixed ROI cropping
- Generating web-optimised proxy media (720p video, MP3 audio) for responsive annotation
- Embedding experimental metadata (mouse IDs, treatment groups) at task import
- Exporting analysis-ready CSV datasets with mouse-resolved behavioural events

Importantly, this tool does **not** perform automated behavioural classification. It supports efficient manual annotation and dataset generation for downstream modelling.

## System Architecture

The platform uses a two-service architecture orchestrated via Docker Compose.

### Components

#### 1. Processor Service (Port 8501)

Custom Streamlit web dashboard responsible for:
- Video ingestion and metadata registration
- Metadata parsing via filename conventions and `mouse_map.csv` lookup
- ROI definition (draw-once, crop-all) and per-mouse video cropping
- Proxy media generation (video and audio)
- Label Studio project creation and task import via REST API
- Annotation export and CSV dataset formatting

**Technology stack:**
| Component | Version |
|---|---|
| Python | 3.9 |
| Streamlit | 1.29.0 |
| FFmpeg | System package (Debian) |
| Docker base image | python:3.9-slim |

#### 2. Annotation Service (Port 8080)

Label Studio provides the annotation interface.

| Component | Version |
|---|---|
| Label Studio | 1.12.1 (heartexlabs/label-studio) |

The processor communicates with Label Studio via REST API.

**Key API functions:**
- Create/update project with XML label configuration
- Import video tasks with embedded metadata
- Create local file storage connections
- Retrieve annotation results via snapshot export

**Authentication:**
API token is auto-retrieved from the Label Studio SQLite database by the processor service. Fallback to username/password session login via CSRF token exchange.

## Data Storage Model

A shared workspace directory serves as the primary data layer. The filesystem acts as the database — no SQL/NoSQL setup is required.

### Structure

```
workspace/
  raw/                  # Input videos (the "Inbox")
    {video_name}/       # Per-video artifact folder (created at registration)
      {video_name}.json       # Metadata sidecar
      {video_name}_proxy.mp4  # Web-optimised video proxy
      {video_name}_audio.mp3  # Audio proxy for waveform rendering
  processed/            # Per-mouse cropped video clips + JSON sidecars
  outputs/              # Exported CSV datasets
  mouse_map.csv         # Group/treatment/mouse-ID lookup table
```

This structure ensures reproducibility and transparent dataset generation.
 
## Metadata System

### Mouse Map

A CSV file (`workspace/mouse_map.csv`) defines the mapping from experimental groups to treatment conditions and mouse IDs (cage positions 1–4):

```csv
Group,Treatment,Cage1,Cage2,Cage3,Cage4
Group 1,Saline-3,212753,211673,213656,214286
Group 2,Fel d 1-6,213695,211674,213657,213106
...
```

### Metadata Sidecar

Each registered video has a JSON sidecar created during ingestion:

```json
{
  "group": "Group 5",
  "treatment": "Control",
  "date": "Dec2",
  "mouse_ids": ["213696", "212754", "212274", "213665"],
  "original_file": "Control_Dec2-024.M4V",
  "full_path": "/workspace/raw/Control_Dec2-024.M4V"
}
```

### Metadata Resolution Order

1. **Filename parsing** — treatment and date extracted from naming convention (e.g., `Control_Dec2-024.M4V` → treatment: `Control`, date: `Dec2`)
2. **`mouse_map.csv` lookup** — treatment matched to group, resolving mouse IDs for all 4 cage positions
3. **Folder structure fallback** — group name matched against parent directory names

Metadata is embedded into Label Studio tasks at import and preserved through the export pipeline.

## Region-of-Interest Cropping

Because animals occupy fixed cage positions, object detection is unnecessary. Instead, a "draw once, crop all" approach is used.

### Workflow

1. User defines 4 ROIs on first frame via an interactive canvas (streamlit-drawable-canvas)
2. Processor applies ROI coordinates to entire video
3. Per-mouse video clips generated using FFmpeg with parallel processing (ThreadPoolExecutor)

### Benefits

- Deterministic cropping
- Reduced computational complexity
- No object tracking errors
- Reusable training clips for future ML work

### FFmpeg Cropping Command

```bash
ffmpeg -i input.mp4 \
  -filter_complex "crop=w:h:x:y" \
  -c:v libx264 -c:a aac -preset veryfast -crf 23 \
  output.mp4
```

Four crops are processed in parallel using `concurrent.futures.ThreadPoolExecutor`.

## Proxy Media Generation

Large video files slow browser playback and annotation. To improve performance, lightweight proxy media are generated.

### Video Proxy

```bash
ffmpeg -y -i input.mp4 \
  -vf "scale=-2:720" \
  -c:v libx264 -crf 26 -preset veryfast \
  -an -movflags +faststart \
  output_proxy.mp4
```

| Parameter | Value |
|---|---|
| Resolution | 720p (width auto-scaled) |
| Codec | H.264 (libx264) |
| CRF | 26 |
| Audio | Removed (separate audio proxy used) |
| Flags | faststart (progressive loading) |

### Audio Proxy

```bash
ffmpeg -y -i input.mp4 \
  -vn -ac 1 -ar 44100 -b:a 64k \
  output_audio.mp3
```

| Parameter | Value |
|---|---|
| Format | MP3 |
| Channels | Mono |
| Sample rate | 44100 Hz |
| Bitrate | 64 kbps |

**Purpose:**
- Waveform rendering on the Label Studio timeline
- Synchronised playback with the video proxy

Proxy generation substantially improves responsiveness (near-instant loading and scrubbing), shifting the bottleneck from media delivery back to the annotator's decision-making.

## Annotation Modes

Two annotation modes are supported via separate Label Studio projects.

### Multi-mouse mode (Primary workflow)

Annotates the full cage view. The researcher labels all 4 mice in a single pass using positional labels: `Rubbing (M1)`, `Rubbing (M2)`, `Rubbing (M3)`, `Rubbing (M4)`.

**Advantages:**
- Faster annotation (1x video duration instead of 4x)
- Preserves spatial context

### Single-mouse mode

Annotates cropped mouse-specific clips with a simplified label set: `Rubbing`, `Eating`, `Active`.

**Advantages:**
- Simplified annotation interface
- Ideal for dataset construction and future ML training

Both modes export mouse-resolved behavioural events.

## Export Pipeline

Annotations are exported as structured tabular CSV data.

### Export columns

```
MouseID, Label_Name, Group, Date, Treatment, Behavior,
Rub_Start_Time, Rub_End_Time, Duration_Seconds,
Video_File, Annotator_ID, Task_ID, Status
```

### Example export

```csv
MouseID,Label_Name,Group,Date,Treatment,Behavior,Rub_Start_Time,Rub_End_Time,Duration_Seconds,Video_File,Annotator_ID,Task_ID,Status
213696,Mouse 1,Group 5,Dec2,Control,Rubbing,42.21,196.98,154.77,Control_Dec2-024_proxy.mp4,1,7,Submitted
212754,Mouse 2,Group 5,Dec2,Control,Rubbing,401.99,600.98,198.99,Control_Dec2-024_proxy.mp4,1,7,Submitted
```

The export pipeline resolves positional labels (`M1`–`M4`) back to individual mouse identifiers using the embedded metadata.

## Dataset Generation

The system produces reusable structured datasets. Output includes:
- Per-mouse behavioural annotations with timestamps and durations
- Aligned experimental metadata (group, treatment, date)
- Reusable cropped video clips (from ROI processing)

**Future extensions:**
- Automated classification via ML models trained on labelled clips
- Automated linking of multi-mouse annotations to per-mouse cropped clips for event-aligned dataset construction
- Behaviour prediction and dataset expansion

## Installation

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running

### Setup

```bash
git clone https://github.com/[ORG_OR_USERNAME]/mouse-behaviour-analysis-tools.git
cd mouse-behaviour-analysis-tools
docker compose up -d
```

### Access

| Service | URL |
|---|---|
| Processor Dashboard | http://localhost:8501 |
| Label Studio | http://localhost:8080 |

Default Label Studio credentials: `user@example.com` / `password123` (configurable in `docker-compose.yml`).

## Workflow Guide

### 1. Ingestion (Registration)

1. Copy raw video files into `workspace/raw/`
2. Open the Processor Dashboard (http://localhost:8501)
3. Go to **Ingestion** page
4. Select a video, verify metadata (auto-parsed from filename and `mouse_map.csv`), and click **Save Metadata & Register**
5. A JSON sidecar is created, making the video available for labelling or cropping

### 2. Labelling (Multi-Mouse) — Primary Workflow

1. Go to **Labelling Queue** page → **Raw Videos (Multi-Mouse)** tab
2. Select registered videos, optionally enable proxy generation (recommended)
3. Click **Upload Raw Videos to Label Studio**
4. Open Label Studio and label all 4 mice per video using positional labels (`Rubbing (M1)`, etc.)

### 3. Optional: ROI Cropping (Single-Mouse Workflow)

1. Go to **ROI Processing** page
2. Select a registered video
3. Draw 4 ROI boxes on the first frame
4. Click **Crop & Process** (parallel processing generates all 4 clips)
5. Go to **Labelling Queue** → **Processed Clips** tab to upload individual clips

### 4. Export Results

1. Go to **Data Export** page
2. Select the Label Studio project
3. Click **Export Data**
4. The exporter maps positional labels (`M1`) back to mouse IDs and saves a CSV to `workspace/outputs/`

## Remote Access (Tailscale)

To access the pipeline from another computer (e.g., for remote labelling):

1. Install [Tailscale](https://tailscale.com/) on both host and client machines
2. Get the Tailscale IP of the host (e.g., `100.x.y.z`)
3. Edit `docker-compose.yml`:
   - `CSRF_TRUSTED_ORIGINS`: add `http://100.x.y.z:8080`
   - `LABEL_STUDIO_PUBLIC_URL`: set to `http://100.x.y.z:8080`
4. Restart: `docker compose up -d`
5. Access via `http://100.x.y.z:8501` (Dashboard) and `http://100.x.y.z:8080` (Label Studio)

## Reproducibility

The system ensures reproducibility via:
- Containerised deployment (identical environment on any OS)
- Version-controlled configuration
- Structured data storage (filesystem-as-database)
- Deterministic preprocessing pipeline

## Repository Contents

```
src/                    # Python application code
  app.py                #   Streamlit dashboard (5 pages)
  setup_workspace.py    #   Workspace directory initializer
  components/           #   UI components (ROI selector, Label Studio XML configs)
  utils/                #   Core logic (video processing, metadata, Label Studio API, export)
docker/                 # Dockerfile and container configuration
  processor/
    Dockerfile
    requirements.txt
docs/                   # Documentation, plans, and guides
workspace/              # Data layer (raw videos, processed clips, exports)
tests/                  # Validation and debugging scripts
docker-compose.yml      # Service orchestration
README.md               # This file
```

## Version Information

| Component | Version |
|---|---|
| Python | 3.9 |
| Docker base image | python:3.9-slim |
| Label Studio | 1.12.1 |
| Streamlit | 1.29.0 |
| FFmpeg | System package via apt (Debian) |
| ffmpeg-python | 0.2.0 |
| OpenCV | opencv-python-headless |
| pandas | 2.1.4 |

<!-- NOTE: For exact FFmpeg build version, run: docker compose exec processor ffmpeg -version -->

## Intended Use

This tool is designed for:
- Behavioural neuroscience
- Immunology studies
- Allergy and infection models
- Translational animal research

## Citation

If used in research, please cite:
[FILL IN MANUSCRIPT REFERENCE]

## Contact

Eva Kaufmann
McGill University
eva.kaufmann@mcgill.ca

## License

MIT License. See [LICENSE](../LICENSE) for details.
