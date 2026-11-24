"""
==============================================================================
Team SkyForge-87: AI-Assisted ESP32 Tiny Drone with Camouflage Image Processing
Module: config.py
Description: Central Configuration Module for Vision Pipeline.
             Change settings in one place without modifying core pipeline code.
==============================================================================
"""

# SOURCE Options:
#   - 0: Laptop webcam (live)
#   - "test.mp4": Video file
#   - "test_images": Folder of CAMO images
#   - "http://192.168.4.1:81/stream": ESP32-CAM MJPEG stream URL
SOURCE = "test.mp4"

# MODEL Selection:
#   - "camouflage" -> U-Net via predict.py (weights: best_model.pth)
#   - "person"     -> YOLOv8n via predict_person.py (weights: yolov8n.pt)
MODEL = "camouflage"

# Preprocessing Settings:
#   - RESIZE: Standard resolution for drone vision (width, height)
#   - USE_CLAHE: Contrast Limited Adaptive Histogram Equalization (default False)
RESIZE = (320, 240)
USE_CLAHE = False

# Pipeline Execution Control:
#   - EVERY_N: Run model inference every N frames (1 = every frame)
EVERY_N = 1

# Performance Target Benchmarks (Mini-Project Targets):
TARGET_MAX_LATENCY_MS = 500.0   # Target: <= 500 ms
TARGET_MIN_FPS = 5.0            # Target: >= 5 FPS
TARGET_MAX_DROP_RATE = 10.0     # Target: < 10%
