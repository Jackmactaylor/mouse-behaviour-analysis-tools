---
title: Phase 3: Motion Heuristics & Pre-annotation
version: 1.0
date_created: 2025-12-17
last_updated: 2025-12-17
---

## Implementation Plan: Phase 3 - Motion Heuristics (HEU)

This phase focuses on optimizing the researcher's time by automatically detecting periods of mouse activity. Instead of manually scrubbing through hours of sleeping mice, the system will pre-scan the video and inject "Active" regions into Label Studio. Researchers can then simply jump between these active regions to classify specific behaviors.

## Architecture and design

**Philosophy:** "Skip the Sleep".
**Core Components:**
1.  **Motion Detector (`src/utils/motion.py`):** A computer vision module using OpenCV to calculate frame-to-frame differences.
2.  **Segmenter:** Logic to convert raw motion scores into discrete time segments (Start/End), handling noise and brief pauses.
3.  **Label Studio Integration:** Updates to the existing client to support uploading `predictions` (pre-annotations) alongside the tasks.

**Design Decisions:**
*   **Pre-annotations vs. TimeSeries:** We chose **Pre-annotations** (Predictions) over simple TimeSeries visualization.
    *   *Reason:* Visualization still requires manual scrubbing. Pre-annotations create actual navigable regions that allow using the "Next Region" hotkey to instantly skip inactive periods.
*   **Processing Stage:** Heuristics will run *after* cropping but *before* upload. This ensures we analyze the specific mouse's activity, not the whole cage rack.
*   **Performance:** Motion detection can be computationally expensive. We will use frame skipping (e.g., analyze every 5th frame) and resizing to ensure it runs quickly on local hardware.

## Supporting Documentation

*   `docs/plans/plan-mouse-labelling-high-level.md`
*   Label Studio Predictions Documentation: https://labelstud.io/guide/predictions.html

## Tasks

- [x] **HEU-01: Motion Detection Module**
    - [x] Create `src/utils/motion.py`.
    - [x] Implement `detect_motion(video_path, sample_rate=5)` function.
    - [x] Logic: Grayscale -> GaussianBlur -> AbsDiff -> Threshold -> Count Non-Zero Pixels.
    - [x] Output: A list of `(timestamp, motion_score)` tuples.

- [x] **HEU-02: Activity Segmentation Logic**
    - [x] Implement `generate_segments(motion_data, threshold, min_duration, merge_gap)`.
    - [x] **Threshold:** Minimum motion score to be considered "moving".
    - [x] **Min Duration:** Ignore blips shorter than X seconds (e.g., 1s).
    - [x] **Merge Gap:** Combine segments if the pause between them is short (e.g., < 2s) to prevent fragmentation.
    - [x] Output: List of `{'start': 10.5, 'end': 15.2, 'label': 'Active'}`.

- [x] **HEU-03: Label Studio Client Update**
    - [x] Update `src/utils/label_studio.py`.
    - [x] Modify `import_tasks` (or create `create_prediction_payload`) to accept a list of regions.
    - [x] Ensure the JSON structure matches Label Studio's `predictions` format:
        ```json
        {
          "model_version": "Heuristic_v1",
          "result": [
            {
              "value": {"start": 10.5, "end": 15.2, "labels": ["Active"]},
              "from_name": "label",
              "to_name": "audio",
              "type": "labels"
            }
          ]
        }
        ```

- [x] **HEU-04: UI Integration**
    - [x] Update `src/app.py` "Labelling Queue" page.
    - [x] Add a checkbox: "Run Motion Detection before Upload".
    - [x] If checked, run `detect_motion` -> `generate_segments` for each video.
    - [x] Include the generated segments in the upload payload.
    - [x] *Update:* Upload as `annotations` (not `predictions`) so they are immediately editable.

- [x] **HEU-05: Configuration Update**
    - [x] Update `src/components/label_studio_config.py` to include an "Active" label if not already present (or decide if we reuse a generic label).
    - [x] *Decision:* Add a specific "Active" label (Gray/Neutral color) that researchers can change to "Rubbing" or delete if it's false positive.

## Open questions & clarifications

1.  **Label Config:** Do we need to add "Active" to the XML config?
    *   *Answer:* Yes, otherwise the pre-annotations might be invalid or invisible. We should add `<Label value="Active" background="lightgray"/>`.
2.  **Threshold Tuning:** How do we set the correct motion threshold?
    *   *Strategy:* We will pick a sensible default (e.g., 1% pixel change) but expose a "Sensitivity" slider in the UI for Phase 3.

## Success criteria

1.  **Accuracy:** The system correctly identifies >90% of actual movement periods (High Recall is preferred over High Precision—we don't want to miss behavior).
2.  **Workflow:** Uploaded tasks in Label Studio show gray "Active" regions on the timeline.
3.  **Navigation:** User can press `Alt + Right Arrow` (or configured hotkey) to jump to the next active region.

## Test plan

1.  **Unit Test:** Run `detect_motion` on a short clip with known movement. Verify scores spike.
2.  **Integration Test:** Process one video, upload with heuristics, and inspect the JSON payload sent to Label Studio.
3.  **E2E Test:** Open the task in Label Studio and verify the regions align with the video movement.
