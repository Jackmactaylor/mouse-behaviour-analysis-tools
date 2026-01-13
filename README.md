# **Mouse Behavior Analysis Pipeline**

A local-first toolkit to streamline the quantification of nasal rubbing incidents in experimental mice.

## **Project Context & Motivation**

This project was built to address a bottleneck in allergy research. Currently, graduate students manually review long video recordings containing 4 mouse cages simultaneously. To quantify nasal rubbing events (a marker of allergic response to FEL D1), they must:

1. Watch the video for *Mouse 1*.  
2. Manually log timestamps of rubbing events.  
3. Rewind and repeat the process for *Mouse 2*, *Mouse 3*, and *Mouse 4*.  
4. Manually map visual data to mouse IDs stored in separate documents.

This manual process is prone to error, extremely time-consuming, and makes capturing precise duration data nearly impossible.

## **The Solution**

This pipeline automates the tedious parts of the workflow, allowing researchers to focus solely on the behavioral classification.

### **Key Features**

* **Fixed ROI Cropping:** Automatically splits a single 4-cage video into 4 individual, stabilized mouse videos using a "draw once, crop all" interface.  
* **Automated Metadata:** Parses the directory structure to automatically tag videos with the correct Mouse ID, Treatment Group, and Date, eliminating lookup errors.  
* **Motion Heuristics:** (Planned) Pre-scans videos to identify periods of inactivity, allowing researchers to skip hours of footage where the mouse is sleeping.  
* **Label Studio Integration:** Uses a containerized instance of [Label Studio](https://labelstud.io/) for a robust labelling interface that captures precise start/stop durations via timeline segmentation.

## **Architecture**

**Philosophy: Local Compute, Cloud Truth.**

* **Storage:** Raw data and final CSV outputs reside in **Google Drive**, ensuring data safety and accessibility for the lab.  
* **Processing:** Heavy lifting (rendering, labelling) happens on the **local machine** to prevent latency and reduce cloud costs.  
* **Environment:** The entire stack runs in **Docker**, ensuring that the tool works identically on a researcher's Windows laptop or the lab's Linux workstation.

## **Getting Started**

*(Note: This project is currently under active development.)*

### **Prerequisites**

* [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running.  

### **Installation**

1. Clone the repository:  
   git clone [https://github.com/your-username/mouse-behavior-analysis.git](https://github.com/your-username/mouse-behavior-analysis.git)  
   cd mouse-behavior-analysis

2. Start the environment:
   ```bash
   docker-compose up -d
   ```

3. Initialize the workspace:
   Create the required folder structure using the container:
   ```bash
   docker-compose exec processor python setup_workspace.py
   ```

4. Access the tools:
   - **Pipeline Dashboard:** [http://localhost:8501](http://localhost:8501)
   - **Label Studio:** [http://localhost:8080](http://localhost:8080)

## **Workflow Guide**

### **1. Ingestion (Crop & Process)**
1. Copy your raw video files into the `workspace/raw` folder (The "Inbox").
2. Open the **Pipeline Dashboard** ([http://localhost:8501](http://localhost:8501)).
3. Go to the **Ingestion** page.
4. Select a video, verify the metadata, and draw 4 boxes around the cages.
5. Click **Process**. This creates 4 individual mouse videos in `workspace/processed`.

### **2. Push to Label Studio**
1. Go to the **Labelling Queue** page in the Dashboard.
2. You will see a list of all processed videos. Select the ones you want to label.
3. Click **Upload Selected Tasks**.
   - *Note:* The system automatically authenticates with Label Studio using the configured environment credentials. No manual API token is required.

### **3. Labelling**
1. Open Label Studio.
2. Enter the **Mouse Behavior Analysis** project.
3. Click **Label All Tasks**.
4. Use the timeline interface (see `docs/labelling_guide.md`) to mark events.

## **Remote Access (Tailscale)**

To access the pipeline from another computer (e.g., viewing results or labelling from a different machine), it is recommended to use [Tailscale](https://tailscale.com/) for a secure, zero-config VPN.

1.  **Install Tailscale**: Install Tailscale on both the host machine (running Docker) and the client machine.
2.  **Get Host IP**: Find the Tailscale IP address of the host machine (e.g., `100.x.y.z`).
3.  **Update Config**: Edit `docker-compose.yml` to trust this IP:
    *   Update `CSRF_TRUSTED_ORIGINS` in the `label-studio` service:
        ```yaml
        - CSRF_TRUSTED_ORIGINS=http://localhost:8080 http://100.x.y.z:8080
        ```
    *   Update `LABEL_STUDIO_PUBLIC_URL` in the `processor` service:
        ```yaml
        - LABEL_STUDIO_PUBLIC_URL=http://100.x.y.z:8080
        ```
4.  **Restart**: Apply changes with `docker-compose up -d`.
5.  **Access**: On the remote machine, access the tools via:
    *   **Pipeline Dashboard:** `http://100.x.y.z:8501`
    *   **Label Studio:** `http://100.x.y.z:8080`

## **Project Structure**

* /src: Python source code for ingestion and processing.  
* /docker: Dockerfile and configuration for the environment.  
* /scripts: Utility scripts for data synchronization.  
* /docs: User guides and architecture diagrams.

## **Contribution**

This tool is designed for internal lab use. Please open an issue for any bugs found during the labelling process.