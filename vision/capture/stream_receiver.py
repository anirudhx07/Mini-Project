"""Video stream receiver supporting Wi-Fi endpoints, video files, and synthetic test feeds."""

import time
import threading
from typing import Optional, Generator
import cv2
import numpy as np

from .frame_buffer import FrameBuffer


class StreamReceiver:
    """Manages video acquisition from network streams or synthetic generators."""

    def __init__(self, source: str = "synthetic", buffer_size: int = 15, target_fps: float = 10.0):
        self.source = source
        self.buffer = FrameBuffer(maxsize=buffer_size)
        self.target_fps = target_fps
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Start asynchronous stream capture thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._capture_worker, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop capture thread cleanly."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)

    def read(self, timeout: float = 1.0) -> tuple[Optional[np.ndarray], float]:
        """Fetch next available frame from buffer."""
        return self.buffer.get(timeout=timeout)

    def _capture_worker(self):
        if self.source == "synthetic":
            self._synthetic_loop()
        else:
            self._network_loop()

    def _synthetic_loop(self):
        """Generates synthetic aerial terrain frames with camouflaged texture patches for testing."""
        frame_interval = 1.0 / self.target_fps
        t = 0.0

        while self._running:
            start_t = time.time()
            t += 0.05

            # Base procedural terrain (grass/soil gradient)
            h, w = 240, 320
            y_coords, x_coords = np.mgrid[0:h, 0:w]
            
            # Simulated aerial terrain texture with natural noise
            base = np.sin(x_coords * 0.04 + t) * np.cos(y_coords * 0.04) * 30 + 100
            noise = np.random.normal(0, 15, (h, w))
            terrain = np.clip(base + noise, 30, 200).astype(np.uint8)

            # 3-channel green-brown foliage palette
            frame = np.zeros((h, w, 3), dtype=np.uint8)
            frame[:, :, 0] = np.clip(terrain * 0.45, 0, 255) # Blue
            frame[:, :, 1] = np.clip(terrain * 0.75 + 20, 0, 255) # Green
            frame[:, :, 2] = np.clip(terrain * 0.50, 0, 255) # Red

            # Inject a camouflaged anomalous patch (blended texture)
            cx = int(160 + np.sin(t * 0.5) * 60)
            cy = int(120 + np.cos(t * 0.5) * 40)
            radius = 22

            # Camouflage patch: subtle texture contrast
            patch_mask = (x_coords - cx)**2 + (y_coords - cy)**2 <= radius**2
            frame[patch_mask, 1] = np.clip(frame[patch_mask, 1] * 0.92 + 10, 0, 255)
            frame[patch_mask, 2] = np.clip(frame[patch_mask, 2] * 1.08, 0, 255)

            self.buffer.put(frame, time.time())

            elapsed = time.time() - start_t
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _network_loop(self):
        """Streams from an IP camera URL or USB index."""
        cap = cv2.VideoCapture(self.source)
        frame_interval = 1.0 / self.target_fps

        while self._running:
            if not cap.isOpened():
                time.sleep(0.5)
                cap.open(self.source)
                continue

            ret, frame = cap.read()
            if ret and frame is not None:
                self.buffer.put(frame, time.time())
            else:
                time.sleep(0.1)

            time.sleep(max(0.001, frame_interval * 0.5))

        cap.release()
