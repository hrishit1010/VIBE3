##Photogrammetry 

## 📝 Overview  
**Photogrammetry** is a high-performance photogrammetry pipeline for reconstructing **accurate 3D models** from multiple 2D images.  
The system integrates state-of-the-art **computer vision** and **geometric processing** methods to perform feature detection, camera pose estimation, dense reconstruction, and mesh generation.  

This project aims to provide a reproducible, modular, and extensible workflow for 3D reconstruction tasks used in research, robotics, and visual computing applications.

---

## ⚙️ Core Features  
- 🖼️ **2D to 3D Reconstruction** — Converts multiple 2D images into detailed, metrically accurate 3D models.  
- 🤖 **Feature Detection and Matching** — Implements robust algorithms (e.g., SIFT, ORB) for keypoint extraction and correspondence.  
- 🧩 **Multiple Reconstruction Methods** — Supports structure-from-motion (SfM) and multi-view stereo (MVS) pipelines.  
- 📐 **Camera Calibration and Alignment** — Performs intrinsic/extrinsic calibration and image registration automatically.  
- 💻 **Cross-Platform Execution** — Compatible with major operating systems and GPU-accelerated processing.  
- 🚀 **Optimized Computation** — Utilizes parallelism and efficient data structures for faster reconstruction performance. 
## 🖼️ Screenshots  

### User Interface  
<img width="1280" height="702" alt="image" src="https://github.com/user-attachments/assets/81f4e5a1-48ca-48aa-956d-5d781a31f70a" />

Workflow
1️⃣ Image Acquisition

Capture a set of overlapping images of the target object from multiple angles.

Maintain uniform lighting and camera stability.

2️⃣ Image Processing

Detect and describe local image features.

Compute pairwise feature correspondences across images.

Estimate camera parameters and scene geometry using bundle adjustment.

3️⃣ 3D Reconstruction

Generate sparse and dense point clouds.

Perform surface reconstruction to generate meshes.

Apply texture mapping to obtain photorealistic 3D output.
##Further ScopeI
ntegration of deep learning-based feature descriptors (SuperPoint, D2-Net)

GPU-based dense reconstruction for real-time performance

Bundle adjustment optimization via Ceres Solver or PyTorch autograd

Export support for GLTF/OBJ formats for 3D rendering pipelines

## 📦 Prerequisites  

Ensure you have the following dependencies installed:  

```bash
pip install opencv-python numpy scipy scikit-image open3d transformations matplotlib plotly
