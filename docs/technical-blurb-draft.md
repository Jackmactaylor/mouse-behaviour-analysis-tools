# Technical Methods — Mouse Behavior Analysis Pipeline

> **Target length:** 1/4–1/2 page in final paper. This draft is intentionally detailed so the researcher can strip it down.

---

## Overview & Prerequisites

The pipeline is a local-first, containerised video analysis tool built with two goals: to accelerate the manual labelling of nasal rubbing behaviour in experimental mice exposed to Fel d 1, and to lay the foundation for a mouse behaviour dataset that could be used to train a classification model in future work. It is designed so that researchers with no software development experience can operate the full system — the only prerequisite on the host machine is [Docker Desktop](https://www.docker.com/products/docker-desktop) (available for Windows, macOS, and Linux). No Python installation, library management, or manual configuration is required on the host. The entire environment is started with a single command:

```bash
docker-compose up -d
```

This launches two Docker containers that together provide the complete processing and annotation stack.

---

## Architecture

The system is composed of two services orchestrated via Docker Compose, communicating through a shared filesystem volume:

```
┌──────────────────────────────────────────────────────┐
│  Host Machine (Docker Desktop)                       │
│                                                      │
│  ┌──────────────────┐       ┌──────────────────┐    │
│  │   Streamlit       │◄─────►│  Label Studio    │    │
│  │   Dashboard       │ REST  │  (HeartexLabs    │    │
│  │   (Port 8501)     │  API  │   v1.12.1)       │    │
│  └────────┬──────────┘       └────────┬─────────┘    │
│           │                           │              │
│           ▼                           ▼              │
│  ┌───────────────────────────────────────────────┐   │
│  │        Shared Volume: /workspace              │   │
│  │   raw/          (input videos + metadata)     │   │
│  │   processed/    (cropped single-mouse clips)  │   │
│  │   outputs/      (exported CSV data)           │   │
│  │   mouse_map.csv (group/treatment lookup)      │   │
│  └───────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

1. **Processor container** — A custom Python 3.9 image running a [Streamlit](https://streamlit.io) web dashboard (port 8501). This service handles video ingestion, metadata registration, FFmpeg-based video processing, and data export. It communicates with Label Studio programmatically via its REST API to create projects, import annotation tasks with embedded metadata, and retrieve completed annotations.

2. **Label Studio container** — An unmodified [HeartexLabs Label Studio v1.12.1](https://labelstud.io/) image (port 8080) providing the annotation interface. It serves video and audio files from the shared volume using its local file serving capability. Annotations are stored in Label Studio's internal SQLite database.

The filesystem acts as the shared data layer between the two containers — no external database is required. Video files, JSON metadata sidecars, and CSV exports all reside in a mounted workspace directory that can be backed up to Google Drive or other lab storage.

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Orchestration | Docker Compose | Multi-container deployment, volume mounting, environment configuration |
| Ingestion & UI | Python 3.9, Streamlit 1.29 | Web dashboard for metadata registration, processing controls, and export |
| Video Processing | FFmpeg (via `ffmpeg-python`), OpenCV | ROI cropping, proxy transcoding, audio extraction |
| Annotation | Label Studio v1.12.1 | Timeline-based behavioural segmentation with custom XML label configurations |
| Data Export | Pandas | JSON-to-CSV transformation with metadata resolution |
| API Integration | Requests | Programmatic Label Studio project management and task import/export |

---

## Key Technical Decisions

### Fixed ROI Cropping (Alternative to Object Detection)

Because mice are housed in fixed cages, the system uses a manual "draw once, crop all" approach rather than object detection (e.g. YOLO, R-CNN). The researcher draws four bounding boxes on the first frame of a video via a Streamlit canvas component. FFmpeg then crops four individual clips in parallel using `ThreadPoolExecutor` (H.264, CRF 23). This avoids the complexity of training or deploying a detection model and is well-suited to the fixed-cage experimental setup.

ROI cropping was the initial approach to annotation, as it served a dual purpose: producing isolated single-mouse clips for labelling one cage at a time, and building a per-mouse video dataset that could later be used to train a nasal rubbing classification model.

### Motion Heuristic Pre-filtering

To reduce the total footage a researcher must review, the pipeline includes a motion detection pre-filter for cropped single-mouse clips. The algorithm calculates pixel intensity changes between consecutive frames; regions that exceed configurable motion and duration thresholds are exported to Label Studio as pre-populated "Active" regions on the annotation timeline. In practice, this reduced watch time by only approximately 10%, as mice are highly active for the majority of the recording and relatively few segments could be confidently classified as inactive.

### Video Proxy Generation

Raw experimental videos are typically large (multi-GB, high resolution). Our recordings are approximately 30 minutes each, though the system is designed to handle longer multi-hour sessions. To ensure responsive playback within Label Studio's web-based player, the pipeline generates optimised proxy files before uploading annotation tasks:

- **Video proxy:** Downscaled to 720p, H.264 encoded with CRF 26, `veryfast` preset, with the `faststart` flag for progressive web loading. Audio is stripped from the video proxy.
- **Audio proxy:** A separate MP3 track extracted from the original video. Label Studio uses this for waveform rendering and synchronised playback.

Both proxies are stored alongside the original in the workspace volume and served to Label Studio via local-file URLs.

### Dual Label Studio Projects

The system maintains two Label Studio projects with different custom XML configurations:

- **Multi-Mouse project:** The researcher annotates all four cages in a single pass of the original (or proxy) video. The interface presents four label groups — `Rubbing (M1)` through `Rubbing (M4)` — mapped to hotkeys `1`–`4`. Each label group targets a specific cage position.
- **Single-Mouse project:** An alternative workflow for individually cropped clips. Uses a simpler label set (`Rubbing`, `Eating`, `Active`) applied to one mouse per video. This workflow also supports playback speed adjustment (2–4×), which can compensate for only reviewing one cage at a time.

In practice, we found that labelling one mouse at a time — even at increased playback speed — was less efficient than observing all four cages simultaneously in the multi-mouse view. However, the ability to split attention across four cages varies between researchers, and some may find the single-mouse workflow preferable. Both workflows remain available.

Importantly, data from the multi-mouse workflow can retrospectively be used to build a per-mouse nasal rubbing dataset. This requires only that ROIs are drawn for each labelled video and the crops processed; the system can then link each mouse ID from the cropped clips to the corresponding entries in the multi-mouse export, yielding per-mouse nasal rubbing duration and event counts tied to individual video files.

When the Streamlit dashboard uploads a video to Label Studio, it creates a task via the REST API that bundles the video URL, audio proxy URL, the four mouse IDs (from registration metadata), and the group/treatment information. During export, the `M1`/`M2`/`M3`/`M4` positional labels are resolved back to actual mouse IDs using this embedded metadata.

### Annotation Interface

Label Studio provides a web-based video player with a synchronised audio waveform timeline. Ideally, annotators would use hotkeys to start and stop labelled regions on the timeline in real-time during playback. However, Label Studio does not natively support hotkey-driven region creation; instead, annotators must pause the video, click and drag on the timeline to define a region, and then assign it a label. This introduces additional interaction overhead per event but remains substantially faster than manual timestamp logging.

### Automated Metadata & Registration

Experimental metadata (date, treatment group, mouse IDs) is derived through a two-stage parsing algorithm and cross-referenced against a `mouse_map.csv` lookup table. The lookup table maps each experimental group to its treatment condition and the four cage-position mouse IDs.

The parsing algorithm operates as follows:

1. **Filename parsing:** The video filename is expected to follow the convention `{Treatment}_{Date}-{index}.ext` (e.g. `Saline-3_Nov20-1.mp4`). The parser splits on the last underscore to extract the treatment string and date component.
2. **Group map matching:** The extracted treatment string is compared against all entries in `mouse_map.csv`. If a match is found, the group name, treatment, and all four cage mouse IDs are populated automatically.
3. **Folder structure fallback:** If the filename does not yield a match, the parser inspects parent directory names for known group identifiers (e.g. a folder named `Group 1: Saline-3`).

In practice, this approach has proved fragile: any deviation in filename spelling or formatting (e.g. a missing hyphen, inconsistent capitalisation) results in no match being found, requiring the researcher to fill metadata fields manually via the dashboard. A future improvement could involve organising videos into per-group folders, or providing an additional mapping file that associates raw video filenames with their experimental groups — potentially merged with the existing mouse map to form a single comprehensive dataset manifest.

Upon registration, the system writes a `.meta.json` sidecar file alongside the video. This sidecar travels with the video through the pipeline and ensures that the final exported CSV contains the correct mouse-level identifiers without manual data entry during annotation.

### API-Driven Label Studio Integration

The pipeline interacts with Label Studio entirely through its REST API — creating projects, configuring label schemas, importing tasks, and exporting annotations. Authentication is handled automatically: the processor container reads the API token directly from Label Studio's SQLite database file (mounted read-only) at startup, removing the need for manual token configuration.

---

## Remote Access via Tailscale

To enable annotation from a second workstation (e.g. for a colleague to label from another room or building), the host machine runs [Tailscale](https://tailscale.com/), a zero-configuration mesh VPN. Tailscale assigns the host a stable private IP address (e.g. `100.x.y.z`). Two environment variables in `docker-compose.yml` are updated to trust this IP:

```yaml
# label-studio service
- CSRF_TRUSTED_ORIGINS=http://localhost:8080 http://100.x.y.z:8080

# processor service
- LABEL_STUDIO_PUBLIC_URL=http://100.x.y.z:8080
```

`CSRF_TRUSTED_ORIGINS` allows Label Studio to accept requests from the Tailscale IP. `LABEL_STUDIO_PUBLIC_URL` ensures the Streamlit dashboard generates video URLs that resolve correctly from the remote machine. After restarting the containers (`docker-compose up -d`), both the dashboard (port 8501) and Label Studio (port 8080) are accessible to any machine on the same Tailscale network using the assigned IP, with no port forwarding or firewall configuration required.

---

## References

- **Label Studio:** Tkachenko, M. et al. (2020–2022). *Label Studio: Data labeling software.* Open Source (Apache 2.0). https://github.com/HumanSignal/label-studio
- **FFmpeg:** FFmpeg Developers. https://ffmpeg.org
- **Streamlit:** Streamlit Inc. https://streamlit.io
- **Docker:** Docker Inc. https://docker.com
- **Tailscale:** Tailscale Inc. https://tailscale.com
