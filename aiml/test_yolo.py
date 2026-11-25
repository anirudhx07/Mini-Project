"""
==============================================================================
Team SkyForge-87: AI-Assisted ESP32 Tiny Drone with Camouflage Image Processing
Unit Tests: test_yolo.py
Description: Pytest validation for YOLOv8n Plan B wrapper (predict_yolo.py):
             1. Model loading.
             2. predict(frame) returns correct annotated frame shape and uint8 dtype.
             3. Detection confidence is bounded in range [0.0, 1.0].
==============================================================================
"""

import os
import sys
import pytest
import numpy as np
import cv2

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from predict_yolo import load_model, predict, _model


def test_yolo_model_loading():
    """Test 1: Verify YOLOv8n weights load correctly."""
    weights_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yolov8n.pt")
    assert os.path.exists(weights_path), f"YOLO weights not found at {weights_path}"
    load_model(weights_path)


def test_yolo_predict_frame_output():
    """
    Test 2: Load one test frame, run predict(frame), and verify:
    - Annotated frame is a valid numpy array with matching shape.
    - Output dtype is uint8.
    - Confidence is bounded in [0.0, 1.0].
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    test_img_dir = os.path.join(base_dir, "test_images")
    img_files = sorted([f for f in os.listdir(test_img_dir) if f.lower().endswith((".jpg", ".png"))])
    assert len(img_files) > 0, "No test images found in test_images/"

    img_path = os.path.join(test_img_dir, img_files[0])
    frame = cv2.imread(img_path)
    assert frame is not None, f"Could not read test image {img_path}"

    annotated, conf = predict(frame)

    # Verify return types and shapes
    assert isinstance(annotated, np.ndarray), "Annotated frame is not a numpy array"
    assert annotated.shape == frame.shape, (
        f"Annotated frame shape {annotated.shape} does not match input frame shape {frame.shape}"
    )
    assert annotated.dtype == np.uint8, f"Expected dtype uint8, got {annotated.dtype}"

    # Verify confidence range
    assert isinstance(conf, float), f"Confidence should be float, got {type(conf)}"
    assert 0.0 <= conf <= 1.0, f"Confidence {conf} out of range [0.0, 1.0]"
