­Manuscript Material and Methods section

AI-assisted behavioural analysis of nasal rubbing in mice

Video acquisition
Mice were videorecorded in their home cages for 30 minutes following each exposure unless otherwise indicated. Three cages (4 mice per cage) were placed in a biological safety cabinet with open lids, and recording was performed using a fixed smartphone camera mounted on the cabinet glass. Cage positions were rotated between experiments to avoid positional bias. Videos were collected in [FILE FORMAT] and totaled approximately [X] hours of footage.

Behavioural event selection and annotation
To enable objective and blinded behavioural quantification, we developed a containerized, local-first video analysis and annotation tool to identify candidate nasal rubbing events. Nasal rubbing was operationally defined as lifting of the forepaws toward the nose region, a movement associated with nasal irritation but also observed during grooming or feeding. The tool reduced video complexity by isolating mouse-specific regions of interest and generating cropped clips for annotation. All candidate events were manually reviewed and classified by a blinded researcher to distinguish nasal rubbing from grooming, feeding, or unrelated movements.

Software architecture and deployment
The system was implemented as a reproducible two-service Docker deployment consisting of (i) a custom processing service for video ingestion, preprocessing, and export, and (ii) Label Studio as the annotation interface. The processor automatically registered videos, embedded experimental metadata, generated annotation tasks via the Label Studio API, and exported structured mouse-level behavioural datasets.

Video preprocessing and performance optimization
Because mice were recorded in fixed cage positions, regions of interest were defined once and applied across videos to generate per-mouse clips using FFmpeg. To improve annotation efficiency, lightweight proxy videos were generated for responsive playback. Optional motion-based filtering was implemented to flag active segments but was used only as a supplementary aid due to high baseline activity levels.

Annotation workflows and dataset generation
Both multi-mouse and single-mouse annotation configurations were supported to maximize annotation efficiency and dataset flexibility. Metadata, including mouse identity and treatment group, were embedded at import and preserved during export. This pipeline enabled efficient, blinded identification and quantification of nasal rubbing events and produced structured datasets suitable for downstream behavioural analysis and future machine learning applications.

Code availability
The video analysis and annotation pipeline developed for this study is available as an open-source, containerized software package. The tool enables reproducible preprocessing, annotation, and export of structured behavioral datasets from multi-mouse video recordings. The complete source code, deployment configuration, annotation schemas, and documentation are available at:
GitHub: https://github.com/[ORG_OR_USERNAME]/[REPOSITORY_NAME]

GitHub Repository README

Mouse Behavior Annotation Tool
Local‑first, containerised video annotation platform for quantifying clinically relevant behavioural patterns in mice, with structured dataset export for downstream analysis and machine learning.

Overview
This tool was developed to support behavioural quantification of nasal rubbing events in mice exposed to inhaled allergens. The platform accelerates manual behavioural annotation while producing structured, reusable datasets suitable for downstream statistical analysis and future machine learning model development.
The system is designed for reproducibility, accessibility, and extensibility. It runs entirely locally using Docker containers, requires no Python installation on the host system, and provides a browser-based interface for efficient annotation.
Primary objectives:
    1. Accelerate manual annotation of clinically relevant behaviour
    2. Generate structured, mouse-level datasets suitable for future automated behavioural classification

Scientific Context
Manual behavioural annotation of laboratory mice from continuous video recordings is time-consuming and prone to inefficiencies due to:
• large video file sizes
• multi-animal recordings
• web playback latency
• lack of structured export formats
This tool addresses these challenges by:
• isolating mouse-specific video regions
• generating web-optimised proxy media
• embedding experimental metadata
• exporting analysis-ready datasets
Importantly, this tool does NOT perform automated behavioural classification. It supports efficient manual annotation and dataset generation for downstream modelling.

System Architecture
The platform uses a two‑service architecture orchestrated via Docker Compose.
Components:
1. Processor Service
Custom web dashboard responsible for:
• video ingestion
• metadata parsing and registration
• ROI definition and cropping
• proxy media generation
• Label Studio project creation via REST API
• annotation export and dataset formatting
Technology stack:
Python: [FILL IN VERSION]
Framework: Streamlit [FILL IN VERSION]
FFmpeg: [FILL IN VERSION]
Docker base image: [FILL IN IMAGE]
2. Annotation Service
Label Studio provides annotation interface.
Label Studio version: [FILL IN VERSION]
The processor communicates with Label Studio via REST API.
Key API functions:
• create project
• upload video tasks
• attach metadata
• retrieve annotation results
Authentication:
[FILL IN TOKEN METHOD]

Data Storage Model
A shared workspace directory serves as the primary data layer.
Structure:
workspace/
videos/        # raw input videos
proxies/       # downscaled proxy videos
cropped/       # per‑mouse video clips
metadata/      # JSON metadata sidecars
exports/       # annotation outputs
projects/      # Label Studio project configs
This structure ensures reproducibility and transparent dataset generation.

Metadata System
Each video has a JSON sidecar file containing experimental metadata.
Example:
{
    "video_id": "VIDEO_001",
    "date": "YYYY-MM-DD",
    "experiment": "cat_dander",
    "group": "treated",
    "mouse_positions": {
        "position_1": "mouse_01",
        "position_2": "mouse_02"
    }
}
Metadata is embedded into annotation tasks and preserved in exports.
Metadata linkage hierarchy:
    1. JSON sidecar (highest priority)
    2. folder structure
    3. filename parsing (fallback)

Region-of-Interest Cropping
Because animals occupy fixed cage positions, object detection is unnecessary.
Instead, a "draw once, crop all" approach is used.
Workflow:
    1. User defines ROIs once
    2. Processor applies ROI coordinates to entire video
    3. Per‑mouse video clips generated using FFmpeg
Benefits:
• deterministic cropping
• reduced computational complexity
• no object tracking errors
• reusable training clips
FFmpeg cropping command:
[FILL IN EXACT COMMAND]

Proxy Media Generation
Large video files slow browser playback and annotation.
To improve performance, lightweight proxy media are generated.
Video proxy:
Resolution: [FILL IN]
Codec: H.264
Bitrate: [FILL IN]
Command:
[FILL IN FFMPEG COMMAND]
Audio proxy:
Codec: AAC
Sample rate: [FILL IN]
Purpose:
• waveform rendering
• synchronized playback
Proxy generation improves responsiveness and annotation throughput.

Annotation Modes
Two annotation modes are supported.
Multi‑mouse mode
Annotates full cage view.
Advantages:
• faster annotation
• preserves spatial context
Single‑mouse mode
Annotates cropped mouse‑specific clips.
Advantages:
• simplified annotation
• ideal for dataset construction
Both modes export mouse-resolved behavioural events.

Export Pipeline
Annotations are exported as structured tabular data.
Export formats:
• CSV
• JSON
Example export:
mouse_id,start_time,end_time,behaviour,group,experiment
mouse_01,12.4,13.7,nasal_rub,treated,cat_dander
Export pipeline resolves positional annotations into mouse identifiers.

Dataset Generation
The system produces reusable structured datasets.
Output includes:
• per-mouse behavioural annotations
• aligned metadata
• reusable cropped video clips
This enables downstream machine learning development.
Future extensions:
• automated classification
• behaviour prediction
• dataset expansion

Installation
Prerequisites:
Docker Desktop
Clone repository:
git clone https://github.com/[FILL IN]
cd mouse-behavior-annotation
Start system:
docker compose up
Access interface:
Processor dashboard:
http://localhost:[FILL IN PORT]
Label Studio:
http://localhost:[FILL IN PORT]

Reproducibility
The system ensures reproducibility via:
• containerised deployment
• version-controlled configuration
• structured data storage
• deterministic preprocessing pipeline

Repository Contents
processor/
annotation/
docker/
docs/
workspace/
README.md

Version Information
Fill in exact versions used for publication reproducibility.
Python: [FILL IN]
Docker: [FILL IN]
Label Studio: [FILL IN]
Streamlit: [FILL IN]
FFmpeg: [FILL IN]

Intended Use
This tool is designed for:
• behavioural neuroscience
• immunology studies
• allergy and infection models
• translational animal research

Citation
If used in research, please cite:
[FILL IN MANUSCRIPT REFERENCE]

Contact
Eva Kaufmann
McGill University
eva.kaufmann@mcgill.ca

License
[FILL IN LICENSE]
