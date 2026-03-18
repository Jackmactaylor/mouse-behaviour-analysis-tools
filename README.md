# Mouse Behavior Analysis Pipeline

A local-first, containerised toolkit to streamline the quantification of nasal rubbing events in experimental mice, with structured dataset export for downstream analysis.

## Project Context & Motivation

This project was built to address a bottleneck in allergy research. Graduate students manually review long video recordings containing 4 mouse cages simultaneously. To quantify nasal rubbing events (a marker of allergic response to Fel d 1), they must:

1. Watch the video for *Mouse 1*.
2. Manually log timestamps of rubbing events.
3. Rewind and repeat the process for *Mouse 2*, *Mouse 3*, and *Mouse 4*.
4. Manually map visual data to mouse IDs stored in separate documents.

This manual process is prone to error, extremely time-consuming, and makes capturing precise duration data nearly impossible.

## The Solution

This pipeline automates the tedious parts of the workflow, allowing researchers to focus solely on the behavioral classification. It does **not** perform automated behavioural classification — it supports efficient manual annotation and structured dataset generation.

### Key Features

* **Fixed ROI Cropping:** Splits a single 4-cage video into 4 individual mouse videos using a "draw once, crop all" interface with parallel processing.
* **Automated Metadata:** Parses filename conventions and a `mouse_map.csv` lookup table to automatically tag videos with Mouse ID, Treatment Group, and Date.
* **Proxy Media Generation:** Creates lightweight 720p video proxies and MP3 audio proxies for responsive browser playback and waveform-based annotation.
* **Motion Heuristics:** Optional pre-scan to flag active video segments via frame-to-frame pixel change detection (supplementary aid).
* **Multi-Mouse Annotation:** Label all 4 mice in a single pass using positional labels (`Rubbing (M1)` through `Rubbing (M4)`), reducing annotation time from 4× to 1× video duration.
* **Label Studio Integration:** Containerised [Label Studio](https://labelstud.io/) instance for timeline segmentation with precise start/stop durations.
* **Structured CSV Export:** Automatic mapping of positional labels back to mouse IDs, producing analysis-ready datasets.

## Architecture

**Philosophy: Local Compute, Local Truth.**

* **Storage:** The filesystem acts as the database. All data lives in the `workspace/` directory — no SQL/NoSQL setup required.
* **Processing:** All video rendering and annotation occurs on the local machine.
* **Environment:** The entire stack runs in **Docker**, ensuring the tool works identically on a researcher's Windows laptop or a Linux workstation.

### System Overview

The platform uses a two-service architecture orchestrated via Docker Compose:

| Service | Port | Description |
|---|---|---|
| **Processor** | 8501 | Streamlit dashboard for ingestion, preprocessing, and export |
| **Label Studio** | 8080 | Annotation interface (heartexlabs/label-studio v1.12.1) |

The processor communicates with Label Studio via REST API to create projects, import tasks with embedded metadata, and retrieve annotations.

## Getting Started

### Prerequisites

* [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Jackmactaylor/mouse-behaviour-analysis-tools.git
   cd mouse-behaviour-analysis-tools
   ```

2. Start the environment:
   ```bash
   docker compose up -d
   ```

3. Access the tools:
   - **Pipeline Dashboard:** [http://localhost:8501](http://localhost:8501)
   - **Label Studio:** [http://localhost:8080](http://localhost:8080)

Default Label Studio credentials: `user@example.com` / `password123` (configurable in `docker-compose.yml`).

## Workflow Guide

### 1. Ingestion (Registration)
1. Copy your raw video files into `workspace/raw/`.
2. Open the **Pipeline Dashboard** ([http://localhost:8501](http://localhost:8501)).
3. Go to the **Ingestion** page.
4. Select a video, verify the auto-parsed metadata (Mouse IDs, Treatment, Date), and click **Save Metadata & Register**.
5. A JSON sidecar is created, making the video available for labelling or cropping.

### 2. Labelling (Multi-Mouse) — Primary Workflow
1. Go to the **Labelling Queue** page → **Raw Videos (Multi-Mouse)** tab.
2. Select registered videos. Enable proxy generation (recommended for faster playback).
3. Click **Upload Raw Videos to Label Studio**.
4. Open Label Studio and label all 4 mice using positional labels (e.g., `Rubbing (M1)`).

### 3. Optional: ROI Cropping (Single-Mouse)
1. Go to the **ROI Processing** page.
2. Select a registered video and draw 4 ROI boxes on the first frame.
3. Click **Crop & Process** (4 clips generated in parallel).
4. Go to **Labelling Queue** → **Processed Clips** tab to upload individual clips.

### 4. Export Results
1. Go to the **Data Export** page.
2. Select the Label Studio project.
3. Click **Export Data**.
   - The exporter maps positional labels (`M1`) back to specific Mouse IDs from the registered metadata.
4. A CSV is saved to `workspace/outputs/`, ready for statistical analysis.

See [`docs/labelling_guide.md`](docs/labelling_guide.md) for detailed annotation instructions including hotkeys and interface tips.

## Metadata System

### Mouse Map

A CSV file (`workspace/mouse_map.csv`) defines group-to-mouse mappings:

```csv
Group,Treatment,Cage1,Cage2,Cage3,Cage4
Group 1,Saline-3,212753,211673,213656,214286
Group 2,Fel d 1-6,213695,211674,213657,213106
```

### Resolution Order

1. **Filename parsing** — treatment and date extracted from naming convention (e.g., `Control_Dec2-024.M4V`)
2. **`mouse_map.csv` lookup** — treatment matched to group, resolving all 4 mouse IDs
3. **Folder structure fallback** — group name matched against parent directory names

## Remote Access (Tailscale)

To access the pipeline from another computer, use [Tailscale](https://tailscale.com/) for a secure, zero-config VPN.

1. Install Tailscale on both the host machine and the client machine.
2. Get the Tailscale IP of the host (e.g., `100.x.y.z`).
3. Edit `docker-compose.yml`:
   - Update `CSRF_TRUSTED_ORIGINS` in the `label-studio` service:
     ```yaml
     - CSRF_TRUSTED_ORIGINS=http://localhost:8080 http://100.x.y.z:8080
     ```
   - Update `LABEL_STUDIO_PUBLIC_URL` in the `processor` service:
     ```yaml
     - LABEL_STUDIO_PUBLIC_URL=http://100.x.y.z:8080
     ```
4. Restart: `docker compose up -d`
5. Access via `http://100.x.y.z:8501` (Dashboard) and `http://100.x.y.z:8080` (Label Studio).

## Project Structure

```
src/                    # Python application code
  app.py                #   Streamlit dashboard (5 pages)
  components/           #   UI components (ROI selector, Label Studio configs)
  utils/                #   Core logic (video processing, metadata, LS API, export)
docker/                 # Dockerfile and container configuration
docs/                   # Labelling guide and developer guidelines
tests/                  # Validation and debugging scripts
workspace/              # Data layer (raw videos, processed clips, CSV exports)
docker-compose.yml      # Service orchestration
LICENSE                 # MIT License
```

## Version Information

| Component | Version |
|---|---|
| Python | 3.9 |
| Docker base image | python:3.9-slim |
| Label Studio | 1.12.1 |
| Streamlit | 1.29.0 |
| ffmpeg-python | 0.2.0 |
| pandas | 2.1.4 |

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Citation

If used in research, please cite:
<!-- TODO: Add manuscript reference when published -->

## Contact

Eva Kaufmann
McGill University
eva.kaufmann@mcgill.ca