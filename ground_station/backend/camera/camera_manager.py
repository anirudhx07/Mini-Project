"""Thread-safe Camera Manager with single capture loop and MJPEG streaming."""

import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, Optional, Tuple
import cv2
import numpy as np

from .base_source import CameraSource
from .webcam_source import WebcamSource
from .esp32cam_source import ESP32CamSource


class CameraManager:
    """Manages active camera source independently of AI inference."""

    def __init__(
        self,
        captures_dir: Path,
        source_type: str = "webcam",
        camera_index: int = 0,
        width: int = 640,
        height: int = 480,
        target_fps: int = 30,
        esp32_cam_url: str = "",
        event_logger=None,
    ):
        self.captures_dir = Path(captures_dir)
        self.captures_dir.mkdir(parents=True, exist_ok=True)
        self._event_logger = event_logger

        self._lock = threading.Lock()
        self.source_type = source_type
        self.camera_index = int(camera_index)
        self.width = int(width)
        self.height = int(height)
        self.target_fps = max(1, min(int(target_fps), 60))
        self.esp32_cam_url = esp32_cam_url

        self._source: Optional[CameraSource] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

        self._latest_frame: Optional[np.ndarray] = None
        self._latest_jpeg: Optional[bytes] = None
        self._frame_id = 0
        self._actual_fps = 0.0
        self._status = "STOPPED"
        self._error_message = ""

    def _build_source(self) -> CameraSource:
        if self.source_type == "esp32cam":
            return ESP32CamSource(stream_url=self.esp32_cam_url)
        return WebcamSource(
            index=self.camera_index,
            width=self.width,
            height=self.height,
            fps=self.target_fps,
        )

    def configure(
        self,
        source_type: Optional[str] = None,
        camera_index: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        target_fps: Optional[int] = None,
        esp32_cam_url: Optional[str] = None,
    ):
        with self._lock:
            if source_type is not None:
                self.source_type = source_type
            if camera_index is not None:
                self.camera_index = int(camera_index)
            if width is not None:
                self.width = int(width)
            if height is not None:
                self.height = int(height)
            if target_fps is not None:
                self.target_fps = max(1, min(int(target_fps), 60))
            if esp32_cam_url is not None:
                self.esp32_cam_url = esp32_cam_url.strip()

    def start(self) -> Tuple[bool, str]:
        """Initialize camera and launch single background capture loop."""
        with self._lock:
            if self._running:
                return True, "Camera already running"
            source = self._build_source()

        ok, msg = source.open()
        if not ok:
            with self._lock:
                self._status = "UNAVAILABLE"
                self._error_message = msg
            if self._event_logger:
                self._event_logger.log("CAMERA", f"Camera start failed: {msg}", level="ERROR")
            return False, msg

        with self._lock:
            self._source = source
            self._running = True
            self._status = "CONNECTED"
            self._error_message = ""
            self._latest_frame = None
            self._latest_jpeg = None
            self._thread = threading.Thread(target=self._capture_loop, name="CameraCaptureLoop", daemon=True)
            self._thread.start()

        if self._event_logger:
            self._event_logger.log("CAMERA", msg, level="INFO")
        return True, msg

    def stop(self):
        """Stop capture loop and release camera hardware."""
        with self._lock:
            was_running = self._running
            self._running = False
            thread = self._thread
            source = self._source
            self._thread = None
            self._source = None

        if thread and thread.is_alive():
            thread.join(timeout=2.0)
        if source is not None:
            source.release()

        with self._lock:
            self._status = "STOPPED"
            self._actual_fps = 0.0
            self._latest_frame = None
            self._latest_jpeg = None

        if was_running and self._event_logger:
            self._event_logger.log("CAMERA", "Camera disconnected and released", level="INFO")

    def _capture_loop(self):
        fps_counter = 0
        fps_timer = time.monotonic()

        while True:
            with self._lock:
                if not self._running or self._source is None:
                    break
                source = self._source
                interval = 1.0 / max(1, self.target_fps)

            t0 = time.monotonic()
            ok, frame = source.read_frame()
            if not ok or frame is None:
                with self._lock:
                    self._status = "DISCONNECTED"
                    self._error_message = "Lost frame stream from camera"
                if self._event_logger:
                    self._event_logger.log("CAMERA", "Camera stream interrupted", level="ERROR")
                break

            ret_enc, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
            jpeg_bytes = buf.tobytes() if ret_enc else None

            fps_counter += 1
            now = time.monotonic()
            elapsed_fps = now - fps_timer

            with self._lock:
                self._latest_frame = frame
                if jpeg_bytes is not None:
                    self._latest_jpeg = jpeg_bytes
                self._frame_id += 1
                self._status = "CONNECTED"
                if elapsed_fps >= 1.0:
                    self._actual_fps = round(fps_counter / elapsed_fps, 1)
                    fps_counter = 0
                    fps_timer = now

            spent = time.monotonic() - t0
            sleep_for = interval - spent
            if sleep_for > 0:
                time.sleep(sleep_for)

        # Ensure release if loop exited abnormally
        with self._lock:
            self._running = False
            if self._source is not None:
                self._source.release()
                self._source = None

    def get_latest_frame(self) -> Tuple[Optional[np.ndarray], int]:
        """Return a copy of the latest BGR frame and its sequence ID."""
        with self._lock:
            if self._latest_frame is None:
                return None, self._frame_id
            return self._latest_frame.copy(), self._frame_id

    def get_latest_jpeg(self) -> Optional[bytes]:
        with self._lock:
            return self._latest_jpeg

    def capture_snapshot(self, prefix: str = "capture", custom_frame: Optional[np.ndarray] = None) -> Tuple[bool, str]:
        """Save current frame or annotated frame into captures/."""
        frame = custom_frame
        if frame is None:
            frame, _ = self.get_latest_frame()
        if frame is None:
            return False, "No active camera frame available to capture"

        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"{prefix}_{ts}.jpg"
        filepath = self.captures_dir / filename
        cv2.imwrite(str(filepath), frame)
        if self._event_logger:
            self._event_logger.log("CAMERA", f"Snapshot saved: {filename}", level="INFO", image_ref=filename)
        return True, filename

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "status": self._status,
                "running": self._running,
                "source_type": self.source_type,
                "source_label": "ESP32-CAM (Future)" if self.source_type == "esp32cam" else f"Laptop Webcam #{self.camera_index}",
                "camera_index": self.camera_index,
                "resolution": f"{self.width}x{self.height}",
                "width": self.width,
                "height": self.height,
                "target_fps": self.target_fps,
                "actual_fps": self._actual_fps,
                "frame_id": self._frame_id,
                "esp32_cam_url": self.esp32_cam_url,
                "error": self._error_message,
            }

    def mjpeg_generator(self) -> Generator[bytes, None, None]:
        """Yield multipart MJPEG frames for Flask streaming endpoint."""
        last_id = -1
        while True:
            with self._lock:
                running = self._running
                jpeg = self._latest_jpeg
                fid = self._frame_id

            if not running:
                break
            if jpeg is not None and fid != last_id:
                last_id = fid
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
                )
            else:
                time.sleep(0.02)
