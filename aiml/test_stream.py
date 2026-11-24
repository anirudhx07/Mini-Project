"""
==============================================================================
Team SkyForge-87: AI-Assisted ESP32 Tiny Drone with Camouflage Image Processing
Unit Tests: test_stream.py
Description: Pytest tests for stream.py FrameSource:
             1. Folder source ends cleanly with 0 failed reads.
             2. Synthetic video file written with cv2.VideoWriter reads correct frame count.
             3. Dead URL stops after small max-failures with dropped % > 0.
             4. Missing file or folder raises clear FileNotFoundError.
==============================================================================
"""

import os
import sys
import pytest
import numpy as np
import cv2

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stream import FrameSource


def test_frame_source_folder():
    """Test 1: Folder source reads all images, ends cleanly with 0 failed reads."""
    folder_path = "test_images"
    assert os.path.exists(folder_path), f"Test folder '{folder_path}' missing."

    expected_count = len([f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
    
    with FrameSource(source=folder_path, loop=False) as src:
        frames_read = 0
        while True:
            frame = src.read()
            if frame is None:
                break
            frames_read += 1
            assert isinstance(frame, np.ndarray)

        # Verified: Reads all images, ends cleanly without failed attempts
        assert frames_read == expected_count
        assert src.failed_reads == 0
        assert src.dropped_frame_percentage == 0.0


def test_frame_source_video_file(tmp_path):
    """Test 2: Video file written with cv2.VideoWriter reads correct frame count and ends cleanly."""
    video_path = str(tmp_path / "synthetic_test.mp4")
    num_frames = 20
    w, h = 160, 120
    fps = 30.0

    # Write a small synthetic video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(video_path, fourcc, fps, (w, h))
    for i in range(num_frames):
        frame = np.full((h, w, 3), (i * 10) % 255, dtype=np.uint8)
        writer.write(frame)
    writer.release()

    # Read back using FrameSource
    with FrameSource(source=video_path, loop=False) as src:
        read_count = 0
        while True:
            frame = src.read()
            if frame is None:
                break
            read_count += 1
            assert frame.shape == (h, w, 3)

        assert read_count == num_frames
        assert src.successful_reads == num_frames
        assert src.failed_reads == 0


def test_frame_source_dead_url():
    """Test 3: Dead URL stops after small max-failures with dropped % > 0."""
    dead_url = "http://localhost:0/x"
    max_failures = 5

    with FrameSource(source=dead_url) as src:
        fail_count = 0
        while fail_count < max_failures:
            frame = src.read()
            if frame is None:
                fail_count += 1
            else:
                break

        assert fail_count == max_failures
        assert src.failed_reads >= max_failures
        assert src.dropped_frame_percentage > 0.0


def test_frame_source_missing_file():
    """Test 4: Non-existent file raises a clear FileNotFoundError."""
    missing_path = "this_file_does_not_exist_at_all_12345.mp4"
    
    with pytest.raises(FileNotFoundError) as exc_info:
        FrameSource(source=missing_path)

    assert "does not exist" in str(exc_info.value)
