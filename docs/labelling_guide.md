# Labelling Guide for Researchers

This guide explains how to use the Label Studio interface to annotate mouse behavior videos. The pipeline supports two annotation modes: **Multi-Mouse** (primary) and **Single-Mouse** (optional, for cropped clips).

## 1. Getting Started

1. Ensure the pipeline is running: `docker compose up -d`
2. Open the **Processor Dashboard** in your browser: [http://localhost:8501](http://localhost:8501)
3. Register your videos via the **Ingestion** page (if not already done).
4. Upload videos to Label Studio via the **Labelling Queue** page.
   - **Raw Videos (Multi-Mouse)** tab → uploads full-frame videos with proxy generation.
   - **Processed Clips (Single Mouse)** tab → uploads individual cropped clips.
5. Open **Label Studio**: [http://localhost:8080](http://localhost:8080)
6. Log in (default: `user@example.com` / `password123` unless changed in `docker-compose.yml`).
7. Select the appropriate project and click **Label All Tasks** to begin.

## 2. The Interface

- **Center:** The video player (showing either the full cage view or a single cropped clip, depending on the project).
- **Bottom:** The audio waveform timeline — this is where you create annotation regions.
- **Right:** The list of regions (labels) you have created for the current video.

> **Note:** Videos are loaded as lightweight proxies (720p) for fast playback. The audio waveform is rendered from a separate MP3 proxy. This is normal and does not affect annotation accuracy.

## 3. How to Label

We use **Time Segments** on the audio waveform timeline to track behavior. This captures the *start time*, *end time*, and *duration* of each event without requiring bounding boxes.

### Multi-Mouse Mode (Primary Workflow)

This is the default mode. You annotate all 4 mice in a single pass of the video.

Each mouse position has its own label:

| Hotkey | Label | Color | Position |
| :--- | :--- | :--- | :--- |
| **1** | Rubbing (M1) | 🔴 Red | Mouse 1 (Left) |
| **2** | Rubbing (M2) | 🟠 Orange | Mouse 2 |
| **3** | Rubbing (M3) | 🟣 Purple | Mouse 3 |
| **4** | Rubbing (M4) | 🩷 Pink | Mouse 4 (Right) |

**Workflow:**
1. **Play the video** (Spacebar) and watch all 4 cage positions.
2. **Pause** when you see a rubbing event.
3. **Press the hotkey** (1–4) for the mouse that is rubbing to activate that label.
4. **Click and drag** on the audio timeline (bottom bar) to mark the start and end of the event.
5. Continue watching and repeat for all rubbing events across all 4 mice.

> **Tip:** You can adjust the start and end points of any region by dragging its handles after creation.

### Single-Mouse Mode (Cropped Clips)

Used when annotating individual per-mouse clips generated via ROI cropping.

| Hotkey | Label | Color |
| :--- | :--- | :--- |
| **1** | Rubbing | 🔴 Red |
| **3** | Eating | 🟢 Green |
| — | Active | 🟠 Orange |

**Workflow:** Same as above, but you only need to watch one mouse at a time.

### General Hotkeys

| Key | Action |
| :--- | :--- |
| **Space** | Play / Pause |
| **Left / Right** | Step frame backward / forward |

## 4. Submitting

- When you are finished labelling a video, click **Submit** (bottom right) or press `Ctrl+Enter`.
- The system will automatically load the next video in the queue.
- If a video has no rubbing events, click **Submit** with no regions — this records it as reviewed with zero events.
- You can also click **Skip** to come back to a video later.

## 5. Exporting Data

Export is handled through the Processor Dashboard — you do not need to export manually from Label Studio.

1. Open the **Processor Dashboard**: [http://localhost:8501](http://localhost:8501)
2. Go to the **Data Export** page.
3. Select the Label Studio project you want to export.
4. Click **Export Data**.
5. The pipeline will:
   - Download annotations from Label Studio via API.
   - Map positional labels (`M1`, `M2`, etc.) back to actual mouse IDs using the registered metadata.
   - Save a CSV file to `workspace/outputs/`.

The exported CSV contains one row per labelled event with columns including: MouseID, Group, Date, Treatment, Behavior, Start/End times, Duration, and more.
