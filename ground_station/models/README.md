# COCKPIT AI Models Directory

Place your local model weights here. COCKPIT does **not** automatically download large models on startup.

## 1. YOLO Object Detection & Tracking

Download a lightweight Ultralytics YOLO model (e.g., `yolov8n.pt`) and place it at:

```
ground_station/models/yolov8n.pt
```

Then ensure `ultralytics` and `torch` are installed:

```powershell
# For NVIDIA RTX 4050 CUDA acceleration:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
pip install ultralytics
```

If CUDA is unavailable, COCKPIT automatically falls back to CPU inference.

## 2. Trained Camouflage Model (Optional)

By default, the **Camouflage Analysis** module runs `BASELINE_VISUAL_ANALYSIS` (LAB color contrast + texture variance + Sobel edge density).  
To plug in a trained camouflage segmentation model later, set `COCKPIT_CAMO_MODEL` in `ground_station/.env`.
