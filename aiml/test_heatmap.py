"""
==============================================================================
Team SkyForge-87: AI-Assisted ESP32 Tiny Drone with Camouflage Image Processing
Unit Tests: test_heatmap.py
Description: Pytest tests for heatmap.py overlay_heatmap:
             1. Output shape and dtype match input frame (H, W, 3) and uint8.
             2. alpha=0 returns the original input frame unchanged.
             3. prob=1 areas are red-dominant while prob=0 areas are blue-dominant in JET colormap.
==============================================================================
"""

import os
import sys
import pytest
import numpy as np
import cv2

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from heatmap import overlay_heatmap, predict_with_prob
import predict as pred_mod


def test_overlay_heatmap_shape_dtype():
    """Test 1: Output shape and dtype match input frame exactly."""
    h, w = 240, 320
    dummy_frame = np.full((h, w, 3), 128, dtype=np.uint8)
    dummy_prob = np.random.uniform(0.0, 1.0, size=(h, w)).astype(np.float32)

    overlay = overlay_heatmap(dummy_frame, dummy_prob, alpha=0.5)

    assert overlay.shape == (h, w, 3), f"Expected shape {(h, w, 3)}, got {overlay.shape}"
    assert overlay.dtype == np.uint8, f"Expected dtype uint8, got {overlay.dtype}"


def test_overlay_heatmap_alpha_zero():
    """Test 2: alpha=0.0 returns the original input frame unchanged."""
    h, w = 100, 100
    test_frame = np.random.randint(0, 256, (h, w, 3), dtype=np.uint8)
    prob_map = np.full((h, w), 0.8, dtype=np.float32)

    # When alpha is 0.0, blending weight for heatmap is 0 and for frame is 1.0
    overlay = overlay_heatmap(test_frame, prob_map, alpha=0.0)

    assert np.array_equal(overlay, test_frame), (
        "overlay_heatmap with alpha=0.0 did not return the original frame."
    )


def test_overlay_heatmap_color_dominance():
    """
    Test 3: In JET colormap:
    - Probability 1.0 (highest confidence) maps to bright Red (R channel dominant).
    - Probability 0.0 (background) maps to bright Blue (B channel dominant).
    """
    h, w = 100, 200
    # Neutral grey background frame so initial color does not bias test
    neutral_frame = np.full((h, w, 3), 100, dtype=np.uint8)

    # Left half: prob = 0.0 (background)
    # Right half: prob = 1.0 (target camouflage detection)
    prob_map = np.zeros((h, w), dtype=np.float32)
    prob_map[:, w // 2:] = 1.0

    overlay = overlay_heatmap(neutral_frame, prob_map, alpha=0.7)

    # Extract Blue and Red channels in BGR format: B=channel 0, R=channel 2
    blue_channel = overlay[:, :, 0]
    red_channel = overlay[:, :, 2]

    # In prob=0 area (left half): Blue must strictly dominate Red
    left_blue_mean = blue_channel[:, :w // 2].mean()
    left_red_mean = red_channel[:, :w // 2].mean()
    assert left_blue_mean > left_red_mean, (
        f"prob=0 area should be blue-dominant, but got Blue={left_blue_mean} <= Red={left_red_mean}"
    )

    # In prob=1 area (right half): Red must strictly dominate Blue
    right_blue_mean = blue_channel[:, w // 2:].mean()
    right_red_mean = red_channel[:, w // 2:].mean()
    assert right_red_mean > right_blue_mean, (
        f"prob=1 area should be red-dominant, but got Red={right_red_mean} <= Blue={right_blue_mean}"
    )


def test_predict_with_prob_matches_predict():
    """
    Test 4: Validate single-pass predict_with_prob():
    - Confidence matches predict() output within 0.01 tolerance.
    - Annotated frame has identical shape.
    - Probability map has shape (H, W) and float32 dtype.
    """
    # Ensure model is initialized
    if pred_mod._model is None:
        pred_mod.load_model("best_model.pth")

    test_img_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_images")
    img_files = sorted([f for f in os.listdir(test_img_dir) if f.lower().endswith((".jpg", ".png"))])
    assert len(img_files) > 0, "No test images found in test_images/"

    img_path = os.path.join(test_img_dir, img_files[0])
    img = cv2.imread(img_path)
    assert img is not None, f"Failed to load image from {img_path}"

    # Run teammate's original predict()
    out_orig, conf_orig = pred_mod.predict(img)

    # Run single-pass predict_with_prob()
    out_single, conf_single, prob_map = predict_with_prob(img)

    # Assert confidence difference <= 0.01
    conf_diff = abs(conf_single - conf_orig)
    assert conf_diff <= 0.01, f"Confidence mismatch: predict={conf_orig}, predict_with_prob={conf_single}, diff={conf_diff}"

    # Assert annotated output shape matches
    assert out_single.shape == out_orig.shape, f"Shape mismatch: {out_single.shape} vs {out_orig.shape}"

    # Assert probability map shape and bounds
    h, w = img.shape[:2]
    assert prob_map.shape == (h, w), f"Prob map shape mismatch: expected {(h, w)}, got {prob_map.shape}"
    assert prob_map.dtype == np.float32, f"Expected float32 prob map, got {prob_map.dtype}"

