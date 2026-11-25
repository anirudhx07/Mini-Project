"""Future ESP32-CAM AI Thinker / OV2640 HTTP MJPEG Stream Adapter."""

from typing import Optional, Tuple
import cv2
import numpy as np

from .base_source import CameraSource


class ESP32CamSource(CameraSource):
    """Adapter for future ESP32-CAM MJPEG stream integration.

    NOTE: ESP32-CAM hardware is not yet attached. When an ESP32-CAM stream URL
    (e.g. http://<esp32-cam-ip>:81/stream) is configured, this adapter connects
    via OpenCV network stream capture without modifying the rest of COCKPIT.
    """

    def __init__(self, stream_url: str = ""):
        self.stream_url = (stream_url or "").strip()
        self._cap: Optional[cv2.VideoCapture] = None

    def open(self) -> Tuple[bool, str]:
        if not self.stream_url:
            return False, "ESP32-CAM stream URL is not configured (hardware not yet integrated)"
        self.release()
        cap = cv2.VideoCapture(self.stream_url)
        if not cap or not cap.isOpened():
            if cap:
                cap.release()
            return False, f"Unable to connect to ESP32-CAM stream at {self.stream_url}"
        self._cap = cap
        return True, f"Connected to ESP32-CAM stream ({self.stream_url})"

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
        return "ESP32-CAM Stream (Future)" if not self.stream_url else f"ESP32-CAM ({self.stream_url})"
