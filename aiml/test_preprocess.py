"""
==============================================================================
Team SkyForge-87: AI-Assisted ESP32 Tiny Drone with Camouflage Image Processing
Unit Tests: test_preprocess.py
Description: Pytest validation for preprocess.py:
             1. Output shape is exactly (240, 320, 3) and dtype is uint8.
             2. When USE_CLAHE is False, image remains completely unchanged.
             3. When USE_CLAHE is True, contrast is enhanced on the L channel.
             4. None input is handled safely without crashing.
==============================================================================
"""

import os
import sys
import pytest
import numpy as np
import cv2

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from preprocess import preprocess, apply_clahe, enhance


def test_preprocess_output_shape_and_dtype():
    """
    Test 1: Output shape must be exactly (240, 320, 3)
    (height=240, width=320, channels=3) and dtype must be uint8.
    """
    raw_frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
    processed = preprocess(raw_frame, target_size=(320, 240), use_clahe=False)

    assert processed.shape == (240, 320, 3), (
        f"Expected shape (240, 320, 3), got {processed.shape}"
    )
    assert processed.dtype == np.uint8, (
        f"Expected dtype uint8, got {processed.dtype}"
    )


def test_preprocess_clahe_off_unchanged():
    """
    Test 2: When USE_CLAHE=False, an image already at target resolution (320x240)
    must remain completely unchanged (bit-for-bit identical).
    """
    frame_320x240 = np.random.randint(0, 256, (240, 320, 3), dtype=np.uint8)
    processed = preprocess(frame_320x240, target_size=(320, 240), use_clahe=False)

    assert np.array_equal(processed, frame_320x240), (
        "preprocess() modified pixel values even when use_clahe was False!"
    )


def test_preprocess_clahe_on_modifies_contrast():
    """
    Test 3: When USE_CLAHE=True, contrast is equalized, modifying pixel values
    while maintaining (240, 320, 3) uint8 format.
    """
    # Create an image with dark and bright regions to give CLAHE contrast work
    test_frame = np.zeros((240, 320, 3), dtype=np.uint8)
    for y in range(240):
        test_frame[y, :, :] = int((y / 240.0) * 160)
    cv2.circle(test_frame, (160, 120), 40, (200, 200, 200), -1)

    processed = preprocess(test_frame, target_size=(320, 240), use_clahe=True)

    assert processed.shape == (240, 320, 3), f"Expected (240, 320, 3), got {processed.shape}"
    assert processed.dtype == np.uint8, f"Expected uint8, got {processed.dtype}"
    assert not np.array_equal(processed, test_frame), (
        "Expected CLAHE to modify pixel contrast, but output matched input exactly."
    )


def test_preprocess_none_safe():
    """Test 4: Passing None to preprocess should return None safely."""
    assert preprocess(None) is None
