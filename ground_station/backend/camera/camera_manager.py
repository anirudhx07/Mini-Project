"""Thread-safe Camera Manager with single capture loop, raw MJPEG passthrough, and auto-reconnect."""

from datetime import datetime
from pathlib import Path
import threading
import time
from typing import Any, Dict, Generator, Optional, Tuple
import urllib.parse
import cv2
import numpy as np

from .base_source import CameraSource
from .webcam_source import WebcamSource
from .esp32cam_source import (
    ESP32CamSource,
    check_esp32cam_health,
    parse_jpeg_dimensions,
    validate_http_url,
)


class CameraManager:
    """Manages active camera source independently of AI inference and flight telemetry."""

    def __init__(
        self,
        captures_dir: Path,
        source_type: str = "esp32cam",
        camera_index: int = 0,
        width: int = 640,
        height: int = 480,
        target_fps: int = 30,
        esp32_cam_url: str = "http://10.159.217.26:81/stream",
        camera_ip: str = "10.159.217.26",
        stream_port: int = 81,
        base_url: str = "http://10.159.217.26",
        auto_reconnect: bool = True,
        connect_timeout: float = 4.0,
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

        self.camera_ip = (camera_ip or "10.159.217.26").strip()
        self.stream_port = int(stream_port)
        self.base_url = (base_url or f"http://{self.camera_ip}").strip().rstrip("/")
        self.esp32_cam_url = (esp32_cam_url or f"http://{self.camera_ip}:{self.stream_port}/stream").strip()
        self.auto_reconnect = bool(auto_reconnect)
        self.connect_timeout = max(1.0, min(float(connect_timeout), 30.0))

        self._source: Optional[CameraSource] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

        self._latest_frame: Optional[np.ndarray] = None
        self._latest_jpeg: Optional[bytes] = None
        self._frame_id = 0
        self._actual_fps = 0.0
        self._latency_ms: Optional[float] = None
        self._detected_resolution: str = ""
        self._last_connected_at: str = ""
        self._status = "DISCONNECTED"
        self._error_message = ""

    def _build_source(self) -> CameraSource:
        if self.source_type == "esp32cam":
            return ESP32CamSource(stream_url=self.esp32_cam_url, timeout=self.connect_timeout)
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
        camera_ip: Optional[str] = None,
        stream_port: Optional[int] = None,
        auto_reconnect: Optional[bool] = None,
        connect_timeout: Optional[float] = None,
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

            if camera_ip is not None and camera_ip.strip():
                self.camera_ip = camera_ip.strip()
                self.base_url = f"http://{self.camera_ip}"
                if esp32_cam_url is None:
                    self.esp32_cam_url = f"http://{self.camera_ip}:{self.stream_port}/stream"

            if stream_port is not None:
                port_val = int(stream_port)
                if not (1 <= port_val <= 65535):
                    raise ValueError("Stream port must be between 1 and 65535")
                self.stream_port = port_val
                if esp32_cam_url is None:
                    self.esp32_cam_url = f"http://{self.camera_ip}:{self.stream_port}/stream"

            if esp32_cam_url is not None:
                cleaned_url = esp32_cam_url.strip()
                if cleaned_url:
                    ok, err = validate_http_url(cleaned_url)
                    if not ok:
                        raise ValueError(err)
                    self.esp32_cam_url = cleaned_url
                    parsed = urllib.parse.urlparse(cleaned_url)
                    if parsed.hostname:
                        self.camera_ip = parsed.hostname
                        self.base_url = f"{parsed.scheme}://{parsed.hostname}"
                    if parsed.port:
                        self.stream_port = parsed.port

            if auto_reconnect is not None:
                self.auto_reconnect = bool(auto_reconnect)
            if connect_timeout is not None:
                self.connect_timeout = max(1.0, min(float(connect_timeout), 30.0))

    def test_connection(self) -> Tuple[bool, str, Optional[float]]:
        """Run a lightweight HTTP reachability check on the configured ESP32-CAM."""
        with self._lock:
            source_type = self.source_type
            base_url = self.base_url
            timeout = self.connect_timeout

        if source_type != "esp32cam":
            return True, "Laptop Webcam mode selected (no network camera probe needed)", 0.0

        ok, msg, latency = check_esp32cam_health(base_url, timeout=timeout)
        with self._lock:
            if latency is not None:
                self._latency_ms = latency
            if not ok and not self._running:
                self._error_message = msg
            elif ok:
                self._error_message = ""
        if self._event_logger:
            self._event_logger.log("CAMERA", msg, level="INFO" if ok else "WARNING")
        return ok, msg, latency

    def start(self) -> Tuple[bool, str]:
        """Initialize camera and launch single background capture loop."""
        with self._lock:
            if self._running:
                return True, "Camera stream already active"
            self._status = "CONNECTING"
            self._error_message = ""
            source = self._build_source()
            is_esp32 = self.source_type == "esp32cam"

        t0 = time.perf_counter()
        ok, msg = source.open()
        conn_ms = round((time.perf_counter() - t0) * 1000.0, 1)

        if not ok:
            with self._lock:
                self._status = "ERROR" if is_esp32 else "UNAVAILABLE"
                self._error_message = msg
                self._latency_ms = None
            if self._event_logger:
                self._event_logger.log("CAMERA", f"Camera start failed: {msg}", level="ERROR")
            return False, msg

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            self._source = source
            self._running = True
            self._status = "CONNECTED"
            self._error_message = ""
            self._latency_ms = conn_ms
            self._last_connected_at = now_str
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
            thread.join(timeout=2.5)
        if source is not None:
            source.release()

        with self._lock:
            self._status = "DISCONNECTED"
            self._actual_fps = 0.0
            self._latest_frame = None
            self._latest_jpeg = None

        if was_running and self._event_logger:
            self._event_logger.log("CAMERA", "Camera stream stopped and released", level="INFO")

    def _capture_loop(self):
        fps_counter = 0
        fps_timer = time.monotonic()
        last_frame_mono = time.monotonic()
        backoff_sec = 2.0

        while True:
            with self._lock:
                if not self._running:
                    break
                source = self._source
                is_esp32 = isinstance(source, ESP32CamSource)
                interval = 1.0 / max(1, self.target_fps)
                auto_reconn = self.auto_reconnect

            if source is None:
                break

            if is_esp32:
                ok, jpeg_bytes = source.read_jpeg()
                frame = None
            else:
                t0 = time.monotonic()
                ok, frame = source.read_frame()
                jpeg_bytes = None
                if ok and frame is not None:
                    ret_enc, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    jpeg_bytes = buf.tobytes() if ret_enc else None

            if not ok or jpeg_bytes is None:
                source.release()
                if is_esp32 and auto_reconn:
                    with self._lock:
                        if not self._running:
                            break
                        self._status = "RECONNECTING"
                        self._actual_fps = 0.0
                        self._error_message = "Stream interrupted — attempting automatic reconnection"
                    if self._event_logger:
                        self._event_logger.log("CAMERA", "ESP32-CAM stream lost; reconnecting...", level="WARNING")

                    # Reconnect loop without blocking Flask
                    reconnected = False
                    while True:
                        with self._lock:
                            if not self._running:
                                break
                            new_src = self._build_source()
                        time.sleep(backoff_sec)
                        with self._lock:
                            if not self._running:
                                break
                        t_rec = time.perf_counter()
                        ok_rec, msg_rec = new_src.open()
                        if ok_rec:
                            rec_ms = round((time.perf_counter() - t_rec) * 1000.0, 1)
                            with self._lock:
                                self._source = new_src
                                self._status = "CONNECTED"
                                self._error_message = ""
                                self._latency_ms = rec_ms
                                self._last_connected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            if self._event_logger:
                                self._event_logger.log("CAMERA", f"ESP32-CAM reconnected ({rec_ms} ms)", level="INFO")
                            backoff_sec = 2.0
                            reconnected = True
                            break
                        else:
                            backoff_sec = min(6.0, backoff_sec + 1.0)
                    if reconnected:
                        fps_counter = 0
                        fps_timer = time.monotonic()
                        last_frame_mono = time.monotonic()
                        continue
                    break

                # Non-auto-reconnect failure
                with self._lock:
                    self._status = "DISCONNECTED"
                    self._actual_fps = 0.0
                    self._error_message = "Lost frame stream from camera"
                if self._event_logger:
                    self._event_logger.log("CAMERA", "Camera stream interrupted", level="ERROR")
                break

            now = time.monotonic()
            frame_dt_ms = round((now - last_frame_mono) * 1000.0, 1)
            last_frame_mono = now
            fps_counter += 1
            elapsed_fps = now - fps_timer

            dims = parse_jpeg_dimensions(jpeg_bytes)
            if dims is None and frame is not None:
                dims = (frame.shape[1], frame.shape[0])

            with self._lock:
                self._latest_frame = frame  # None for ESP32-CAM until decoded lazily
                self._latest_jpeg = jpeg_bytes
                self._frame_id += 1
                self._status = "STREAMING"
                self._error_message = ""
                if is_esp32 and frame_dt_ms > 0:
                    self._latency_ms = frame_dt_ms
                if dims is not None:
                    self._detected_resolution = f"{dims[0]}x{dims[1]}"
                if elapsed_fps >= 1.0:
                    self._actual_fps = round(fps_counter / elapsed_fps, 1)
                    fps_counter = 0
                    fps_timer = now

            if not is_esp32:
                spent = time.monotonic() - t0
                sleep_for = interval - spent
                if sleep_for > 0:
                    time.sleep(sleep_for)

        with self._lock:
            self._running = False
            if self._source is not None:
                self._source.release()
                self._source = None

    def get_latest_frame(self) -> Tuple[Optional[np.ndarray], int]:
        """Return a copy of the latest BGR frame (lazily decoding JPEG for ESP32-CAM)."""
        with self._lock:
            frame = self._latest_frame.copy() if self._latest_frame is not None else None
            jpeg = self._latest_jpeg
            fid = self._frame_id

        if frame is not None:
            return frame, fid
        if jpeg is not None:
            arr = np.frombuffer(jpeg, dtype=np.uint8)
            decoded = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            return decoded, fid
        return None, fid

    def get_latest_jpeg(self) -> Optional[bytes]:
        with self._lock:
            return self._latest_jpeg

    def capture_snapshot(self, prefix: str = "capture", custom_frame: Optional[np.ndarray] = None) -> Tuple[bool, str]:
        """Save original full-resolution JPEG frame (or custom annotated BGR frame) into captures/."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"{prefix}_{ts}.jpg"
        filepath = self.captures_dir / filename

        if custom_frame is not None:
            cv2.imwrite(str(filepath), custom_frame)
            if self._event_logger:
                self._event_logger.log("CAMERA", f"Snapshot saved: {filename}", level="INFO", image_ref=filename)
            return True, filename

        jpeg = self.get_latest_jpeg()
        if jpeg is not None:
            with open(filepath, "wb") as f:
                f.write(jpeg)
            if self._event_logger:
                self._event_logger.log("CAMERA", f"Full-res snapshot saved: {filename}", level="INFO", image_ref=filename)
            return True, filename

        return False, "No active camera frame available to capture"

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            is_esp32 = self.source_type == "esp32cam"
            res_str = self._detected_resolution or (f"{self.width}x{self.height}" if not is_esp32 else "Unknown")
            return {
                "status": self._status,
                "running": self._running,
                "source_type": self.source_type,
                "camera_name": "ESP32-CAM OV2640" if is_esp32 else f"Laptop Webcam #{self.camera_index}",
                "source_label": "ESP32-CAM OV2640" if is_esp32 else f"Laptop Webcam #{self.camera_index}",
                "camera_index": self.camera_index,
                "camera_ip": self.camera_ip,
                "stream_port": self.stream_port,
                "base_url": self.base_url,
                "esp32_cam_url": self.esp32_cam_url,
                "auto_reconnect": self.auto_reconnect,
                "connect_timeout": self.connect_timeout,
                "resolution": res_str,
                "width": self.width,
                "height": self.height,
                "target_fps": self.target_fps,
                "actual_fps": self._actual_fps,
                "latency_ms": self._latency_ms,
                "last_connected_at": self._last_connected_at or None,
                "frame_id": self._frame_id,
                "error": self._error_message,
            }

    def mjpeg_generator(self) -> Generator[bytes, None, None]:
        """Yield raw multipart MJPEG frames directly to Flask without re-encoding."""
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
                    b"Content-Type: image/jpeg\r\n"
                    + f"Content-Length: {len(jpeg)}\r\n\r\n".encode("ascii")
                    + jpeg
                    + b"\r\n"
                )
            else:
                time.sleep(0.015)
