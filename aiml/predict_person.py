"""
==============================================================================
Team SkyForge-87: AI-Assisted ESP32 Tiny Drone with Camouflage Image Processing
Module: predict_person.py
Description: Plan B Person Tracking Model Interface (YOLOv8n).
             Matches exact interface of predict.py:
             - load_model(path="best_model.pth"): loads yolov8n.pt (ignores path)
             - predict(frame) -> (annotated_frame, confidence)
==============================================================================
"""

import os
import numpy as np
from ultralytics import YOLO

_model = None


def load_model(path: str = "best_model.pth"):
    """
    Load YOLOv8n model for person detection and tracking.
    'path' is ignored because yolov8n.pt is loaded directly.
    """
    global _model
    weights_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yolov8n.pt")
    if not os.path.exists(weights_path):
        weights_path = "yolov8n.pt"
    _model = YOLO(weights_path)


def predict(frame: np.ndarray):
    """
    Run YOLOv8n person tracking on an input BGR frame.

    :param frame: OpenCV BGR image (H, W, 3), dtype uint8.
    :return: (annotated_frame, confidence)
             annotated_frame: Frame with bounding boxes/IDs, same size (H, W, 3).
             confidence: Highest person confidence in [0.0, 1.0], or 0.0 if none.
    """
    global _model
    if _model is None:
        load_model()

    if frame is None or frame.size == 0:
        return frame, 0.0

    # Sequence tracking with person class (0), conf=0.4, imgsz=320
    results = _model.track(
        frame,
        classes=[0],       # 0 = Person class in COCO
        conf=0.4,
        persist=True,
        imgsz=320,
        verbose=False
    )

    res = results[0]
    annotated = res.plot()

    if res.boxes is not None and len(res.boxes) > 0 and len(res.boxes.conf) > 0:
        conf = float(res.boxes.conf.max().item())
    else:
        conf = 0.0

    return annotated, conf
