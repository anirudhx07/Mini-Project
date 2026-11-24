"""
==============================================================================
Team SkyForge-87: AI-Assisted ESP32 Tiny Drone with Camouflage Image Processing
Unit Tests: test_pipeline.py
Description: Pytest validation for pipeline integration without loading AI models:
             1. Folder source yields valid video frames.
             2. Mock predict (frame -> (frame.copy(), 0.0)) runs cleanly through the pipeline.
==============================================================================
"""

import os
import sys
import pytest
import numpy as np

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stream import FrameSource
from pipeline import run_pipeline


def test_folder_source_yields_frames():
    """
    Test: Folder source se frames aaye.
    Loads from test_images/ and verifies valid BGR uint8 frame acquisition.
    """
    folder_path = "test_images"
    assert os.path.exists(folder_path), f"Test images directory '{folder_path}' missing."

    src = FrameSource(source=folder_path, loop=False)
    frame = src.read()
    src.release()

    assert frame is not None, "Failed to read initial frame from folder source."
    assert isinstance(frame, np.ndarray), "Acquired frame is not a numpy array."
    assert frame.dtype == np.uint8, "Frame dtype is not uint8."
    assert len(frame.shape) == 3 and frame.shape[2] == 3, f"Unexpected frame shape {frame.shape}"


def test_mock_predict_in_pipeline():
    """
    Test: Predict ka mock (frame -> (frame.copy(), 0.0)) pipeline mein chale.
    Runs pipeline without loading PyTorch or YOLO models.
    """
    mock_predict_called = []

    def mock_predict(frame: np.ndarray):
        mock_predict_called.append(True)
        # Mock interface returning untouched copy and 0.0 confidence
        return frame.copy(), 0.0

    summary = run_pipeline(
        source="test_images",
        model_type="camouflage",
        use_clahe=False,
        predict_fn=mock_predict,
        max_frames=3,
        display=False
    )

    assert summary["frames"] == 3, f"Expected 3 frames processed, got {summary['frames']}"
    assert len(mock_predict_called) == 3, f"Mock predict called {len(mock_predict_called)} times, expected 3"
    assert summary["drop_pct"] == 0.0, f"Expected 0% drop rate, got {summary['drop_pct']}"
