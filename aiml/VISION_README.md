# AI-Assisted ESP32 Tiny Drone — Computer Vision & Preprocessing Pipeline
### Author: Priyanshu (Computer Vision & Pipeline Owner) | Team SkyForge-87

---

## 📌 Executive Summary

This module contains the real-time ground-station Computer Vision (CV) Pipeline for the **AI-Assisted ESP32 Tiny Drone**. The pipeline acquires video frames from the drone (or test sources), standardizes image resolution, applies optional contrast enhancement (CLAHE on the LAB L-channel), performs neural inference, overlays visual explainability heatmaps, and tracks performance telemetry in real time on laptop CPU hardware.

---

## 🏗️ Architecture & Pipeline Flow

```text
[ Video Input Source ]
  ├── ESP32-CAM MJPEG Stream (http://<ip>:81/stream)
  ├── Mobile IP Webcam (http://<ip>:8080/video)
  ├── Laptop Integrated Webcam (0)
  ├── Recorded Drone Video (*.mp4)
  └── Offline Test Image Dataset (test_images/)
           │
           ▼
   [ stream.py : FrameSource ]
   - Automatic 3-attempt reconnection on connection drops
   - Frame dropped rate counter & hardware capture FPS tracking
           │
           ▼
   [ preprocess.py : preprocess() ]
   - Standardization to target resolution: 320x240 (Width x Height)
   - Optional CLAHE on Lightness (L) channel in LAB color space
   - Preserves natural colors without chromatic distortion
           │
           ▼
   [ pipeline.py : Model Dispatch ]
   ├── Plan A: U-Net Camouflage Segmentation (predict.py, best_model.pth)
   │     └── Single-Pass Explainability Heatmap (heatmap.py, COLORMAP_JET)
   └── Plan B: YOLOv8n Person Tracking (predict_person.py, yolov8n.pt)
           │
           ▼
   [ Visualization & Telemetry ]
   - Side-by-Side Display: Original (320x240) | Result (+ Heatmap)
   - Real-time OSD: Latency (ms), Confidence Score, Processing FPS
   - Key 'S': Saves snapshot to results/ and logs to results_log.csv
   - Exit Summary: Logs run metrics to run_summary.csv
```

---

## 📁 Vision Pipeline Modules

| File | Primary Responsibility |
| :--- | :--- |
| **`pipeline.py`** | Unified end-to-end vision pipeline runner. Integrates stream acquisition, preprocessing, dual-model dispatch, single-pass heatmap explainability, and telemetry. |
| **`preprocess.py`** | Centralized image preprocessor. Standardizes frames to (320, 240) and applies optional CLAHE contrast equalization on the L-channel of LAB space (`use_clahe=False` by default). |
| **`stream.py`** | Robust `FrameSource` class wrapping OpenCV video capture. Features 3 reconnection retries on connection loss, EOF detection, and dropped-frame telemetry. |
| **`heatmap.py`** | Visual explainability module. Generates `cv2.COLORMAP_JET` pseudo-color heatmaps and features single-pass `predict_with_prob()` eliminating redundant U-Net forward passes. |
| **`predict_person.py`** | Plan B person tracking wrapper around Ultralytics YOLOv8n (`yolov8n.pt`). Replicates the exact function interface of `predict.py` for seamless drop-in interoperability. |
| **`config.py`** | Central configuration hub defining input sources (`SOURCE`), model selection (`MODEL`), CLAHE flags (`USE_CLAHE`), and performance targets. |
| **`eval_clahe.py`** | Quantitative evaluation benchmark comparing CAMO dataset predictions across Plain, CLAHE 1.0, CLAHE 2.0, and CLAHE 4.0 settings. |
| **`clahe_analysis.md`** | Statistical analysis of evaluation results, reporting per-image IoU changes, median improvements, and distribution metrics. |

---

## 🧪 Comprehensive Automated Test Suite

All unit tests are designed to execute in seconds without requiring GPU hardware or loading heavy neural network weights:

| Test File | Verification Target |
| :--- | :--- |
| **`test_preprocess.py`** | Validates output shape `(240, 320, 3)` uint8, verifies image is bit-for-bit unchanged when `use_clahe=False`, and confirms contrast modification when `use_clahe=True`. |
| **`test_stream.py`** | Tests clean folder iteration, video file frame counts, fast dead-URL failure handling (< 1s), and non-existent file exceptions. |
| **`test_pipeline.py`** | Injects a lightweight mock model (`lambda f: (f.copy(), 0.0)`) to verify end-to-end pipeline execution and frame acquisition without AI dependencies. |
| **`test_heatmap.py`** | Validates output shape and uint8 dtype, checks alpha blending (`alpha=0` returns original), verifies JET colormap dominance, and confirms output parity with `predict()`. |
| **`test_yolo.py`** | Verifies YOLOv8n model loading, output array shape matching input frame, and confidence bounded in range `[0.0, 1.0]`. |
| **`test_enhance.py`** | Tests legacy `enhance()` helper for backward compatibility and confirms neutral grey images experience zero chromatic shift. |

---

## 📊 Performance Benchmarks (Laptop CPU)

*Hardware: Intel64 Family 6 Model 191 Stepping 2, GenuineIntel (PyTorch CPU Engine)*  
*Source: `test.mp4` (140 benchmarked frames after 10 warm-up frames)*

| Configuration | Model Architecture | Heatmap Explainability | Latency (ms) | Inference FPS | Dropped Frames | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Standard Inference** | U-Net (Camouflage) | Disabled (`off`) | **58.1 ms** | **17.2 FPS** | **0.0%** | **PASS** |
| **Single-Pass Heatmap** | U-Net (Camouflage) | Enabled (`on`) | **57.5 ms** | **17.4 FPS** | **0.0%** | **PASS** |
| **Plan B Tracking** | YOLOv8n (Person) | N/A (Bounding box) | **28.2 ms** | **35.5 FPS** | **0.0%** | **PASS** |

### Target Verification:
- **Average Latency**: $\le 500\text{ ms}$ $\rightarrow$ **Achieved: 57.5 ms** (**PASS**)
- **Processing Rate**: $\ge 5.0\text{ FPS}$ $\rightarrow$ **Achieved: 17.4 FPS** (**PASS**)
- **Dropped Frame Rate**: $< 10.0\%$ $\rightarrow$ **Achieved: 0.0%** (**PASS**)

---

## 🚀 How to Run

### 1. Execute Vision Pipeline
```bash
# Default run (settings from config.py):
python aiml/pipeline.py

# Benchmark with Single-Pass Explainability Heatmap:
python aiml/pipeline.py --source test.mp4 --heatmap on --bench 150

# Live Mobile Stream (IP Webcam) or ESP32-CAM:
python aiml/pipeline.py --source http://172.16.189.20:8080/video

# Run Plan B (Person Detection & Tracking):
python aiml/pipeline.py --source 0 --model person
```

### 2. Run Automated Tests
```bash
python -m pytest aiml/test_preprocess.py aiml/test_stream.py aiml/test_pipeline.py -v
```

### 3. Run Quantitative Evaluation
```bash
python aiml/eval_clahe.py
```

---

## ⌨️ Runtime Controls
- **`S` Key**: Saves the current side-by-side annotated snapshot to `results/` and appends telemetry metadata to `results_log.csv`.
- **`ESC` Key**: Gracefully stops the video stream, releases camera hardware resources, and prints the performance summary report.
