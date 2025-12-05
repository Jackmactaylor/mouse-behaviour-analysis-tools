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
* **Label Studio Integration:** Uses a containerized instance of [Label Studio](https://labelstud.io/) for a robust, keyboard-driven labelling interface that captures precise start/stop durations.

## **Architecture**

**Philosophy: Local Compute, Cloud Truth.**

* **Storage:** Raw data and final CSV outputs reside in **Google Drive**, ensuring data safety and accessibility for the lab.  
* **Processing:** Heavy lifting (rendering, labelling) happens on the **local machine** to prevent latency and reduce cloud costs.  
* **Environment:** The entire stack runs in **Docker**, ensuring that the tool works identically on a researcher's Windows laptop or the lab's Linux workstation.

## **Getting Started**

*(Note: This project is currently under active development.)*

### **Prerequisites**

* [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running.  
* Access to the Lab Google Drive (mounted via Google Drive for Desktop recommended).

### **Installation**

1. Clone the repository:  
   git clone \[https://github.com/your-username/mouse-behavior-analysis.git\](https://github.com/your-username/mouse-behavior-analysis.git)  
   cd mouse-behavior-analysis

2. Start the environment:  
   docker-compose up \-d

3. Access the tools:  
   * **Label Studio:** http://localhost:8080  
   * **Ingestion Tool:** (Command to run script to be added)

## **Project Structure**

* /src: Python source code for ingestion and processing.  
* /docker: Dockerfile and configuration for the environment.  
* /scripts: Utility scripts for data synchronization.  
* /docs: User guides and architecture diagrams.

## **Contribution**

This tool is designed for internal lab use. Please open an issue for any bugs found during the labelling process.