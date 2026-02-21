# Mouse Behaviour Analysis Pipeline Technical Summary

 *(Tool creation justification and dual purpose statement)* 

To support behavioural quantification of nasal rubbing events in mice exposed to Fel d 1, we developed a local-first, containerised video analysis and annotation tool with two objectives: 

(i) accelerating manual labelling of nasal rubbing behaviour, and 

(ii) producing a structured, mouse-level dataset suitable for future model training and reuse. 

The system was intentionally designed so that non-developer researchers could run the full stack without installing a Python environment or managing dependencies on the host machine; the only prerequisite is a standard container runtime (Docker Desktop), with the complete environment launched as a reproducible multi-service deployment.

 *(Architecture overview and vague stack, could mention details for versions of Python, Docker, Streamlit, etc. if necessary)* 

The implementation uses a two-service architecture orchestrated via Docker Compose and a shared workspace directory. A custom “processor” service (implemented as a lightweight web dashboard) handles video ingestion, metadata registration, video preprocessing, and export of annotation results into analysis-ready tabular formats. A second service runs Label Studio as the annotation interface. The processor communicates with Label Studio through its REST API to create or configure projects, register videos as annotation tasks with embedded experimental metadata, and retrieve completed annotations for downstream analysis; the shared filesystem volume functions as the primary data layer, containing raw videos, derived media (e.g., cropped clips and proxies), metadata sidecars, and exports.

 *(Justification of ROIs over Object Detection, normally AI datasets need object detection because things move but the mice are in cages so a region also works and doesn’t risk periods where the mouse is obscured. Discovery of motion detection being mostly useless could be cut as wasn’t used in the final workflow)* 

Several technical design decisions were driven by constraints observed during tool development and early use. Because animals were recorded in fixed cage positions, the pipeline adopted a “draw once, crop all” approach rather than deploying object detection: the user defines cage/mouse regions of interest (ROIs) on an initial frame, and the processor generates per-mouse cropped clips from the source video using FFmpeg-based transforms. This choice both reduced implementation complexity and created isolated, mouse-specific video assets that can be reused as training examples in future classification work. An optional motion-based pre-filtering step was also implemented to mark candidate “active” segments via frame-to-frame pixel change heuristics; however, because mice were active for much of each recording, this strategy provided only minimal reduction in total viewing time and was treated as an assistive, not primary, speedup mechanism.

 *(Discovery of internet speed being a primary bottleneck)* 

The most consequential performance discovery was that annotation throughput was often bottlenecked not by human labelling speed but by web playback latency when loading large, high-resolution source videos in the browser, particularly under slow or unstable network conditions. To address this, the processor generates lightweight proxy media before task creation: a downscaled, web-optimised video proxy for responsive streaming, and a separate audio proxy for fast waveform rendering and synchronised playback within Label Studio. In practice, proxy generation substantially improved responsiveness (near-instant loading and scrubbing), making the annotation interface viable on constrained connections and shifting the limiting factor back to the annotator’s decision-making rather than media delivery.

To accommodate different annotation preferences while preserving flexibility for dataset construction, the system maintains two complementary Label Studio project configurations:

1) a multi-mouse view (annotating all cage positions within a single video using distinct positional labels) and   
2) a single-mouse view (annotating one cropped clip at a time with a simplified label set). 

In practice, multi-mouse annotation was generally more time-efficient; however, the single-mouse configuration remained valuable for cases where splitting attention across multiple cages was less comfortable, and for scenarios where mouse-specific clips are preferred for dataset assembly. 

 *(This is a future work/extension idea and explains how (ii) from the intro could be achieved but not completely necessary)* 

Additionally, ROI cropping can be applied retrospectively to recordings annotated in the multi-mouse project to generate per-mouse video clips. However, automated linking of these derived single-mouse videos to the annotated rubbing intervals is not currently implemented and would require an extension to the existing export and indexing logic; implementing this linkage would enable construction of an event-aligned dataset for downstream model training. 

 *(More somewhat tedious dataset details but might be useful for people wanting to extend the code or build the dataset mentioned previous)* 

Across both modes, task metadata (mouse IDs, treatment/group information) is embedded at import time and later used to resolve positional labels back to individual mouse identifiers during export; metadata is derived via automated parsing and lookup (with a JSON sidecar written alongside each video), though development experience highlighted that filename-based conventions can be fragile and benefit from stricter data manifests or folder-level organization. Full configuration details, deployment files, and label schemas are available in the project Git repository. 