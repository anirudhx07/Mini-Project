"""
==============================================================================
Team SkyForge-87: AI-Assisted ESP32 Tiny Drone with Camouflage Image Processing
Unit Tests: test_enhance.py
Description: Pytest unit tests for the enhance() function imported from preprocess.py:
             1. Output shape is exactly (240, 320, 3)
             2. Output data type is uint8
             3. Output pixels differ from input (contrast enhanced)
             4. Colours are not badly shifted on a neutral grey image
==============================================================================
"""

import os
import sys
import pytest
import numpy as np
import cv2

# Ensure current directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Task 1: Import enhance from preprocess.py
from preprocess import enhance


def test_enhance_output_shape():
    """Test 1: Output shape must be exactly (240, 320, 3) -> height 240, width 320, 3 channels."""
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    enhanced = enhance(dummy_frame)
    
    assert enhanced.shape == (240, 320, 3), (
        f"Expected shape (240, 320, 3), but got {enhanced.shape}"
    )


def test_enhance_dtype():
    """Test 2: Output data type must be uint8 for standard image display and model compatibility."""
    dummy_frame = np.ones((100, 100, 3), dtype=np.uint8) * 128
    enhanced = enhance(dummy_frame)
    
    assert enhanced.dtype == np.uint8, (
        f"Expected dtype uint8, but got {enhanced.dtype}"
    )


def test_enhance_output_differs_from_input():
    """Test 3: Output must differ from input when contrast can be enhanced."""
    test_frame = np.zeros((240, 320, 3), dtype=np.uint8)
    for y in range(240):
        test_frame[y, :, :] = int((y / 240.0) * 160)
    
    cv2.circle(test_frame, (160, 120), 40, (200, 200, 200), -1)

    enhanced = enhance(test_frame)
    
    assert not np.array_equal(test_frame, enhanced), (
        "Enhanced image pixel values are identical to input; CLAHE did not modify the image."
    )


def test_enhance_no_colour_shift_on_grey():
    """
    Test 4: On a neutral grey image (R=G=B), CLAHE on the L channel of LAB space
    must not introduce false colour tints (A and B channels remain unaffected).
    """
    grey_gradient = np.tile(
        np.linspace(40, 220, 320, dtype=np.uint8),
        (240, 1)
    )
    grey_bgr = np.dstack([grey_gradient, grey_gradient, grey_gradient])
    
    enhanced = enhance(grey_bgr)
    b, g, r = cv2.split(enhanced)
    
    diff_bg = np.abs(b.astype(int) - g.astype(int))
    diff_gr = np.abs(g.astype(int) - r.astype(int))
    diff_br = np.abs(b.astype(int) - r.astype(int))
    
    max_chroma_shift = max(diff_bg.max(), diff_gr.max(), diff_br.max())
    
    assert max_chroma_shift <= 2, (
        f"Colours were badly shifted on a neutral grey image! Max channel difference: {max_chroma_shift}"
    )
