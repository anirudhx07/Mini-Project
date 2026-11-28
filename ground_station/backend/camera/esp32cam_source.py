"""ESP32-CAM AI Thinker / OV2640 HTTP MJPEG Stream Adapter & Health Probe."""

import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional, Tuple
import cv2
import numpy as np

from .base_source import CameraSource


def parse_jpeg_dimensions(jpeg_bytes: bytes) -> Optional[Tuple[int, int]]:
    """Extract (width, height) from JPEG SOF0/SOF2 marker without full image decode."""
    if not jpeg_bytes or len(jpeg_bytes) < 4 or jpeg_bytes[0:2] != b"\xff\xd8":
        return None
    i = 2
    n = len(jpeg_bytes)
    while i + 9 < n:
        if jpeg_bytes[i] != 0xFF:
            i += 1
            continue
        marker = jpeg_bytes[i + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            height = int.from_bytes(jpeg_bytes[i + 5 : i + 7], "big")
            width = int.from_bytes(jpeg_bytes[i + 7 : i + 9], "big")
            if width > 0 and height > 0:
                return (width, height)
            return None
        if marker in (0xD8, 0xD9, 0x01) or (0xD0 <= marker <= 0xD7):
            i += 2
            continue
        if i + 4 >= n:
            break
        seg_len = int.from_bytes(jpeg_bytes[i + 2 : i + 4], "big")
        if seg_len < 2:
            break
        i += 2 + seg_len
    return None


def validate_http_url(url: str) -> Tuple[bool, str]:
    """Validate that a camera URL is a well-formed HTTP/HTTPS endpoint."""
    cleaned = (url or "").strip()
    if not cleaned:
        return False, "ESP32-CAM stream URL is not configured"
    parsed = urllib.parse.urlparse(cleaned)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False, f"Invalid camera URL '{cleaned}'. Expected http://<ip>:<port>/stream"
    return True, cleaned


def check_esp32cam_health(base_url: str, timeout: float = 3.0) -> Tuple[bool, str, Optional[float]]:
    """Perform a lightweight HTTP reachability check without opening an MJPEG stream."""
    ok, msg_or_url = validate_http_url(base_url)
    if not ok:
        return False, msg_or_url, None

    t0 = time.perf_counter()
    req = urllib.request.Request(msg_or_url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=float(timeout)) as resp:
            status = getattr(resp, "status", 200)
            latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)
            if 200 <= status < 400:
                return True, f"ESP32-CAM reachable at {msg_or_url} (HTTP {status}, {latency_ms} ms)", latency_ms
            return False, f"ESP32-CAM returned HTTP {status}", latency_ms
    except urllib.error.HTTPError as exc:
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)
        if exc.code < 500:
            return True, f"ESP32-CAM host reachable (HTTP {exc.code}, {latency_ms} ms)", latency_ms
        return False, f"ESP32-CAM HTTP error {exc.code}", latency_ms
    except (urllib.error.URLError, socket.timeout, TimeoutError, OSError) as exc:
        return False, f"ESP32-CAM unreachable at {msg_or_url}: {exc}", None


class ESP32CamSource(CameraSource):
    """Low-latency raw HTTP MJPEG reader for AI Thinker ESP32-CAM OV2640."""

    def __init__(self, stream_url: str = "", timeout: float = 4.0):
        self.stream_url = (stream_url or "").strip()
        self.timeout = max(1.0, min(float(timeout), 30.0))
        self._resp = None
        self._buf = bytearray()

    def open(self) -> Tuple[bool, str]:
        ok, msg_or_url = validate_http_url(self.stream_url)
        if not ok:
            return False, msg_or_url
        self.release()

        try:
            req = urllib.request.Request(msg_or_url, headers={"Connection": "close"})
            resp = urllib.request.urlopen(req, timeout=self.timeout)
            status = getattr(resp, "status", 200)
            if status >= 400:
                resp.close()
                return False, f"ESP32-CAM stream returned HTTP {status}"
            self._resp = resp
            self._buf.clear()
            return True, f"Connected to ESP32-CAM stream ({msg_or_url})"
        except (urllib.error.URLError, socket.timeout, TimeoutError, OSError) as exc:
            return False, f"Unable to connect to ESP32-CAM at {msg_or_url}: {exc}"
        except Exception as exc:
            return False, f"ESP32-CAM connection error: {exc}"

    def read_jpeg(self) -> Tuple[bool, Optional[bytes]]:
        """Read next raw JPEG frame directly from the MJPEG HTTP stream without decoding."""
        if self._resp is None:
            return False, None

        try:
            while True:
                soi = self._buf.find(b"\xff\xd8")
                if soi != -1:
                    eoi = self._buf.find(b"\xff\xd9", soi + 2)
                    if eoi != -1:
                        jpeg = bytes(self._buf[soi : eoi + 2])
                        del self._buf[: eoi + 2]
                        return True, jpeg
                    if soi > 0:
                        del self._buf[:soi]

                chunk = self._resp.read(16384)
                if not chunk:
                    return False, None
                self._buf.extend(chunk)

                if len(self._buf) > 2 * 1024 * 1024:
                    self._buf.clear()
                    return False, None
        except (socket.timeout, TimeoutError, OSError, urllib.error.URLError):
            return False, None
        except Exception:
            return False, None

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Decode raw JPEG into BGR numpy array when requested by CV/AI modules."""
        ok, jpeg = self.read_jpeg()
        if not ok or not jpeg:
            return False, None
        arr = np.frombuffer(jpeg, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            return False, None
        return True, frame

    def release(self):
        if self._resp is not None:
            try:
                self._resp.close()
            except Exception:
                pass
            self._resp = None
        self._buf.clear()

    def is_opened(self) -> bool:
        return self._resp is not None

    def source_name(self) -> str:
        return "ESP32-CAM OV2640"
