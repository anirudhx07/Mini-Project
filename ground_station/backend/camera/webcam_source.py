"""Laptop Webcam Camera Adapter using OpenCV."""

import platform
from typing import Optional, Tuple
import cv2
import numpy as np

from .base_source import CameraSource


class WebcamSource(CameraSource):
    """OpenCV VideoCapture adapter for local laptop/USB webcams."""

    def __init__(self, index: int = 0, width: int = 640, height: int = 480, fps: int = 30):
        self.index = int(index)
        self.width = int(width)
        self.height = int(height)
        self.fps = int(fps)
        self._cap: Optional[cv2.VideoCapture] = None

    def open(self) -> Tuple[bool, str]:
        self.release()
        backend = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY
        cap = cv2.VideoCapture(self.index, backend)
        if not cap or not cap.isOpened():
            if cap:
                cap.release()
            # Fallback to default backend
            cap = cv2.VideoCapture(self.index)
        if not cap or not cap.isOpened():
            if cap:
                cap.release()
            return False, f"Camera device index {self.index} unavailable or in use"

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_FPS, self.fps)

        ret, test_frame = cap.read()
        if not ret or test_frame is None:
            cap.release()
            return False, f"Camera index {self.index} opened but failed to deliver frames"

        self._cap = cap
        actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or self.width)
        actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or self.height)
        return True, f"Webcam #{self.index} initialized ({actual_w}x{actual_h})"

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        if self._cap is None or not self._cap.isOpened():
            return False, None
        ret, frame = self._cap.read()
        if not ret or frame is None:
            return False, None
        return True, frame

    def release(self):
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None

    def is_opened(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def source_name(self) -> str:
        return f"Laptop Webcam (Index {self.index})"
