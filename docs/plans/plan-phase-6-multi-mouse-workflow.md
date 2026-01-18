---
title: Multi-Mouse Workflow Migration
version: 1.0
date_created: 2026-01-16
last_updated: 2026-01-16
---

## Implementation Plan: Multi-Mouse Workflow Migration

The goal is to shift the primary workflow from "Crop -> Label" to "Label Original (4 mice) -> Optional Crop". This reduces the time burden on researchers by allowing them to watch 4 mice simultaneously.

## Architecture and design

### 1. Page Restructuring (`src/app.py`)
*   **Split "Ingestion":** The current Ingestion page is too heavy. It will be split into:
    1.  **Ingestion (Metadata Only):** Focuses solely on registering raw videos and creating a standardized metadata sidecar (`.json`) in `/workspace/raw`.
    2.  **ROI Processing (Optional):** A new page that reads the registered videos and offers the ROI cropping functionality.

### 2. Metadata Sidecars
*   We will introduce a distinct JSON sidecar for raw videos in `/workspace/raw`.
*   **Format:**
    ```json
    {
      "original_file": "212753_Dec2_Control.mp4",
      "group": "Group 5",
      "treatment": "Control",
      "date": "Dec2",
      "mouse_ids": ["212274", "212754", "213665", "213696"],
      "created_at": "..."
    }
    ```
*   This sidecar acts as the "Registration" proof, making the video visible to both the Labelling Queue and the ROI Processing page.

### 3. Labelling Queue & Label Studio
*   **Two Queues:** The Labelling Queue page will display two tabs/sections:
    *   **Raw Videos (Multi-Mouse):** Videos from `/workspace/raw` with sidecars.
    *   **Processed Clips (Single Mouse):** Videos from `/workspace/processed`.
*   **Project Strategy:** 
    *   To avoid configuration conflicts (View config for 1 vs 4 mice), we will use **two separate Label Studio projects**:
        1.  `Mouse Behavior Analysis (Cropped)` - The existing one.
        2.  `Mouse Behavior Analysis (Multi-Mouse)` - A new project.
    *   The `LabelStudioClient` will need to manage these project names or IDs dynamically.
*   **Label Configuration (Multi-Mouse):**
    *   We will use a config that supports unique labels per mouse (e.g., `Rubbing (M1)`, `Rubbing (M2)`).
    *   Alternative: Use one generic `Rubbing` label but separate `RectangleLabels` regions if we used bounding boxes (but user wants timeline segmentation).
    *   *Decision:* We will use 4 sets of labels or distinct values like `M1_Rubbing`, `M2_Rubbing` to ensure the CSV export can map back to the correct Mouse ID.

### 4. Data Export
*   `src/utils/data_exporter.py` must support the new label format.
*   Logic:
    *   If Project is "Multi-Mouse": Parse label `M1_Rubbing` -> Look up index 0 in `mouse_ids` metadata -> Assign specific MouseID.
    *   If Project is "Cropped": Use existing logic (1 video = 1 MouseID).

## Tasks

### Phase 1: App Restructuring & Ingestion
- [x] **REF-01**: Create `src/pages/` structure or simply refactor `src/app.py` to support cleaner page definitions (optional refactor, might just stick to `if page == ...` for simplicity given the constraints).
- [x] **ING-01**: Modify "Ingestion" page to remove ROI/Processing logic.
- [x] **ING-02**: Implement "Save Metadata" button that writes the JSON sidecar to `/workspace/raw`.
- [x] **ROI-01**: Create new "ROI Processing" page in sidebar.
- [x] **ROI-02**: Implement logic to read registered raw videos (via JSONs) and allow selecting them for the existing ROI workflow.

### Phase 2: Labelling Queue & Project Management
- [x] **Q-01**: Update "Labelling Queue" to tabs: "Raw Videos" and "Processed Clips".
- [x] **Q-02**: Implement scanning logic for raw video sidecars.
- [x] **LS-01**: Define `LABEL_STUDIO_MULTI_CONFIG` in `src/components/label_studio_config.py` with labels for 4 mice (M1..M4).
- [x] **LS-02**: Update `app.py` upload logic to select/create the correct project (`Mouse Behavior Analysis (Multi)` vs `(Cropped)`).
- [x] **LS-03**: Modify import payload for raw videos to include the full `mouse_ids` list in `meta` data.

### Phase 3: Data Export & Documentation
- [x] **EXP-01**: Update `process_export_to_csv` in `data_exporter.py` to detect project type or label format.
- [x] **EXP-02**: Implement mapping logic: `Label="M1_Rubbing"` + `Meta.mouse_ids=["A","B","C","D"]` -> `Row(MouseID="A", Behavior="Rubbing")`.
- [x] **DOC-01**: Update `README.md` to reflect new workflow.
- [ ] **DOC-02**: Update `docs/labelling_guide.md` (if exists) or create note about multi-mouse labelling.

## Open questions & clarifications

1.  **Label Format:** Is `M1_Rubbing` sufficient? Yes, as long as the UI clearly constructs the timeline.
2.  **Number of Mice:** We assume 4 for now. If a video has 3, the 4th label set will just be unused.

## Success criteria

1.  User can register a raw video and immediately see it in Labelling Queue.
2.  User can upload raw video to Label Studio and see 4 distinct label options (or sets).
3.  Exporting data from a Multi-Mouse project results in a CSV with correct individual Mouse IDs.
4.  Legacy ROI workflow still functions from its new page.
