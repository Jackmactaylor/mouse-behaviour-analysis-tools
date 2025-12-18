# **Labelling Guide for Researchers**

This guide explains how to use the Label Studio interface to annotate mouse behavior videos efficiently.

## **1. Getting Started**

1.  Ensure the pipeline is running (`docker-compose up -d`).
2.  Open **Label Studio** in your browser: [http://localhost:8080](http://localhost:8080).
3.  Log in (default: `user@example.com` / `password123` unless changed).
4.  Click on the **Mouse Behavior Analysis** project.
5.  Click the blue **Label All Tasks** button to start a session.

## **2. The Interface**

*   **Center:** The video player.
*   **Bottom:** The timeline and audio waveform (if applicable).
*   **Right:** The list of regions (labels) you have created.

## **3. How to Label**

We use **Time Segments** to track behavior. This allows us to capture the *duration* and *frequency* of events without needing to draw bounding boxes.

### **Workflow**

1.  **Play the video** (Spacebar).
2.  When you see a behavior start (e.g., Rubbing):
    *   **Press the Hotkey** (e.g., `1` for Rubbing).
    *   A colored region will start appearing on the timeline.
3.  When the behavior stops:
    *   **Press the Hotkey again** (e.g., `1`).
    *   The region stops recording.
    *   *Tip:* You can drag the ends of the region in the timeline to adjust the start/end times precisely if you missed the exact moment.

### **Hotkeys**

| Key | Action | Label Color |
| :--- | :--- | :--- |
| **1** | **Rubbing** (Nasal rubbing/scratching) | 🔴 Red |
| **2** | **Grooming** (General body grooming) | 🔵 Blue |
| **3** | **Eating** | 🟢 Green |
| **Space** | Play / Pause | |
| **Left / Right** | Step frame backward / forward | |

## **4. Submitting**

*   When you are finished with a video, click **Submit** (bottom right) or press `Ctrl+Enter`.
*   The system will automatically load the next video in the queue.
*   If a video has no relevant behaviors, you can just click **Submit** (or **Skip** if enabled).

## **5. Exporting Data**

(Note: This will be automated in Phase 5, but manual export is always possible)

1.  Go to the Project Dashboard.
2.  Click **Export**.
3.  Choose **CSV** or **JSON**.
