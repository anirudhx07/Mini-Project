"""
==============================================================================
Team SkyForge-87: AI-Assisted ESP32 Tiny Drone with Camouflage Image Processing
Module: stream.py
Description: Video Capture and Frame Acquisition Management.
             Wraps cv2.VideoCapture with tracking for:
             - Total reads & successful reads
             - Failed reads & dropped-frame percentage
             - Hardware / Stream Capture FPS (with n/a handling for offline sources)
==============================================================================
"""

import sys
import os
import time
from typing import Optional, Union
import cv2
import numpy as np


class FrameSource:
    """
    Robust video capture stream wrapper for Webcams, ESP32-CAM streams,
    video files, and test image folders.
    """
    def __init__(self, source: Union[int, str] = 0, buffer_size: int = 1, loop: bool = False):
        self.source = source
        self.buffer_size = buffer_size
        self.loop = loop
        
        self.is_folder = False
        self.is_url = False
        self.is_video_file = False
        self.is_webcam = False
        
        self.cap: Optional[cv2.VideoCapture] = None
        self._folder_files = []
        self._folder_idx = 0
        
        # Performance and dropped frame telemetry
        self.total_reads = 0
        self.successful_reads = 0
        self.failed_reads = 0
        self.start_time = None
        self.last_read_time = None
        self._recent_timestamps = []
        self.was_ever_opened = False
        self.reconnect_count = 0

        self._initialize_source()
        if self.cap is not None and self.cap.isOpened():
            self.was_ever_opened = True

    def _initialize_source(self):
        """Set up hardware capture, video file, or folder iteration with error handling."""
        # 1. Integer Webcam Source
        if isinstance(self.source, int):
            self.is_webcam = True
            if sys.platform.startswith("win"):
                self.cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
            else:
                self.cap = cv2.VideoCapture(self.source)

            try:
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)
            except Exception:
                pass
            return

        # String Source
        source_str = str(self.source).strip()

        # Numeric string (e.g. "0")
        if source_str.isdigit():
            self.is_webcam = True
            dev_idx = int(source_str)
            if sys.platform.startswith("win"):
                self.cap = cv2.VideoCapture(dev_idx, cv2.CAP_DSHOW)
            else:
                self.cap = cv2.VideoCapture(dev_idx)
            return

        # 2. Network Stream URL (ESP32-CAM / RTSP / HTTP)
        source_lower = source_str.lower()
        if source_lower.startswith(("http://", "https://", "rtsp://")):
            self.is_url = True
            self.cap = cv2.VideoCapture(source_str)
            try:
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)
            except Exception:
                pass
            return

        # 3. Local Folder Source
        if os.path.isdir(source_str):
            self.is_folder = True
            self._folder_files = sorted([
                os.path.join(source_str, f)
                for f in os.listdir(source_str)
                if f.lower().endswith(('.jpg', '.jpeg', '.png'))
            ])
            self._folder_idx = 0
            return

        # 4. Local Video File Source
        if os.path.isfile(source_str):
            self.is_video_file = True
            self.cap = cv2.VideoCapture(source_str)
            return

        # 5. Missing File / Folder -> Raise clear error
        raise FileNotFoundError(
            f"[Stream Error] Input source '{source_str}' does not exist as a file, folder, or valid URL."
        )

    @property
    def is_live(self) -> bool:
        """Return True if source is a live hardware or network stream (webcam/URL)."""
        return self.is_webcam or self.is_url

    def is_opened(self) -> bool:
        """Check if camera, video, or folder source is ready."""
        if self.is_folder:
            return len(self._folder_files) > 0
        return self.cap is not None and self.cap.isOpened()

    def reconnect(self, max_retries: int = 3, retry_delay: float = 0.1) -> bool:
        """
        Attempt to reconnect to live camera or network stream up to 3 times
        when the connection drops.
        """
        if not self.is_live:
            return False

        for attempt in range(1, max_retries + 1):
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            time.sleep(retry_delay)
            try:
                self._initialize_source()
                if self.cap is not None and self.cap.isOpened():
                    return True
            except Exception:
                pass
        return False

    def read(self) -> Optional[np.ndarray]:
        """
        Acquire a single frame from the stream.
        
        :return: np.ndarray frame if successful, None on failure or EOF.
        """
        now = time.perf_counter()
        if self.start_time is None:
            self.start_time = now

        # Case A: Folder Source
        if self.is_folder:
            if self._folder_idx < len(self._folder_files):
                self.total_reads += 1
                file_path = self._folder_files[self._folder_idx]
                self._folder_idx += 1
                frame = cv2.imread(file_path)
                if frame is not None:
                    self.successful_reads += 1
                    self.last_read_time = now
                    self._record_timestamp(now)
                    return frame
                else:
                    self.failed_reads += 1
                    return None

            # Handle end of folder
            if self.loop and len(self._folder_files) > 0:
                self._folder_idx = 0
                return self.read()

            # Clean end of folder (not counted as failed attempt)
            return None

        # Case B: Video File or Stream Source
        self.total_reads += 1
        if self.cap is None or not self.cap.isOpened():
            # For live streams that previously dropped, attempt reconnect up to 3 times
            if self.is_live and self.was_ever_opened and self.reconnect_count < 3:
                if self.reconnect(max_retries=3):
                    ok, frame = self.cap.read()
                    if ok and frame is not None:
                        self.successful_reads += 1
                        self.last_read_time = now
                        self._record_timestamp(now)
                        return frame

            self.failed_reads += 1
            return None

        ok, frame = self.cap.read()
        if ok and frame is not None:
            self.successful_reads += 1
            self.last_read_time = now
            self._record_timestamp(now)
            return frame

        # End of video file reached
        if self.is_video_file and self.loop:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self.cap.read()
            if ok and frame is not None:
                self.successful_reads += 1
                self.last_read_time = now
                self._record_timestamp(now)
                return frame

        # For video file without loop, end-of-file is clean; for live streams, it's a drop
        if self.is_video_file and not self.loop:
            # Do not penalize natural video EOF as dropped frame
            self.total_reads -= 1
            return None

        # For live streams (webcam/URL), attempt 3 reconnects on dropped connection
        if self.is_live and self.was_ever_opened and self.reconnect_count < 3:
            if self.reconnect(max_retries=3):
                ok, frame = self.cap.read()
                if ok and frame is not None:
                    self.successful_reads += 1
                    self.last_read_time = now
                    self._record_timestamp(now)
                    return frame

        self.failed_reads += 1
        return None

    def _record_timestamp(self, ts: float):
        """Maintain a rolling window of recent timestamps for smooth FPS calculation."""
        self._recent_timestamps.append(ts)
        if len(self._recent_timestamps) > 60:
            self._recent_timestamps.pop(0)

    @property
    def capture_fps(self) -> Optional[float]:
        """
        Calculate actual hardware/stream capture rate in Frames Per Second.
        Returns None for offline sources (folder, video file) as requested.
        """
        if not self.is_live:
            return None

        if len(self._recent_timestamps) >= 2:
            duration = self._recent_timestamps[-1] - self._recent_timestamps[0]
            if duration > 0:
                return (len(self._recent_timestamps) - 1) / duration

        if self.start_time and self.last_read_time:
            total_duration = self.last_read_time - self.start_time
            if total_duration > 0:
                return self.successful_reads / total_duration

        return 0.0

    @property
    def dropped_frame_percentage(self) -> float:
        """Return percentage of failed frame reads out of total read attempts."""
        if self.total_reads == 0:
            return 0.0
        return (100.0 * self.failed_reads) / self.total_reads

    def release(self):
        """Release underlying hardware resources safely."""
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
            self.cap = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
