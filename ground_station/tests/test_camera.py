"""Tests for Camera Abstraction, Initialization, Unavailability Handling, and Shutdown."""

from http.server import BaseHTTPRequestHandler, HTTPServer
import io
import sys
import threading
import time
from pathlib import Path
import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.camera.base_source import CameraSource
from backend.camera.camera_manager import CameraManager
from backend.camera.esp32cam_source import ESP32CamSource, parse_jpeg_dimensions, validate_http_url


class _FakeCameraSource(CameraSource):
    def __init__(self, should_open=True):
        self.should_open = should_open
        self.opened = False

    def open(self):
        if not self.should_open:
            return False, "Simulated unavailable camera"
        self.opened = True
        return True, "Fake camera opened"

    def read_frame(self):
        if not self.opened:
            return False, None
        return True, np.zeros((120, 160, 3), dtype=np.uint8)

    def release(self):
        self.opened = False

    def is_opened(self):
        return self.opened

    def source_name(self):
        return "FakeCamera"


def test_esp32cam_unconfigured_fails_gracefully():
    src = ESP32CamSource(stream_url="")
    ok, msg = src.open()
    assert ok is False
    assert "not configured" in msg.lower()


def test_camera_start_and_shutdown(tmp_path):
    cm = CameraManager(captures_dir=tmp_path)
    fake = _FakeCameraSource(should_open=True)
    cm._build_source = lambda: fake

    ok, _ = cm.start()
    assert ok is True
    assert cm.get_status()["running"] is True

    # Wait briefly for capture loop to grab a frame
    import time
    time.sleep(0.1)
    frame, fid = cm.get_latest_frame()
    assert frame is not None
    assert fid >= 1

    snap_ok, fname = cm.capture_snapshot(prefix="test")
    assert snap_ok is True
    assert (tmp_path / fname).exists()

    cm.stop()
    assert cm.get_status()["running"] is False
    assert cm.get_status()["status"] == "DISCONNECTED"
    assert fake.is_opened() is False


def test_camera_unavailable_handling(tmp_path):
    cm = CameraManager(captures_dir=tmp_path, source_type="webcam")
    cm._build_source = lambda: _FakeCameraSource(should_open=False)
    ok, msg = cm.start()
    assert ok is False
    assert cm.get_status()["status"] == "UNAVAILABLE"
    assert cm.get_status()["running"] is False


def test_parse_jpeg_dimensions_vga():
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", img)
    assert ok is True
    dims = parse_jpeg_dimensions(buf.tobytes())
    assert dims == (640, 480)


def test_validate_http_url():
    ok, _ = validate_http_url("http://10.159.217.26:81/stream")
    assert ok is True
    bad, _ = validate_http_url("not-a-url")
    assert bad is False


def test_esp32cam_mjpeg_stream_and_snapshot(tmp_path):
    img = np.full((480, 640, 3), (40, 120, 200), dtype=np.uint8)
    _, jpg_buf = cv2.imencode(".jpg", img)
    jpg_bytes = jpg_buf.tobytes()

    class _MockCamHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def do_GET(self):
            if self.path == "/stream":
                self.send_response(200)
                self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
                self.end_headers()
                for _ in range(30):
                    try:
                        self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg_bytes + b"\r\n")
                        self.wfile.flush()
                        time.sleep(0.03)
                    except OSError:
                        break
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')

    server = HTTPServer(("127.0.0.1", 0), _MockCamHandler)
    port = server.server_address[1]
    srv_thread = threading.Thread(target=server.serve_forever, daemon=True)
    srv_thread.start()

    cm = CameraManager(
        captures_dir=tmp_path,
        source_type="esp32cam",
        camera_ip="127.0.0.1",
        stream_port=port,
        base_url=f"http://127.0.0.1:{port}",
        esp32_cam_url=f"http://127.0.0.1:{port}/stream",
        auto_reconnect=False,
        connect_timeout=2.0,
    )
    try:
        ok_probe, _, _ = cm.test_connection()
        assert ok_probe is True

        ok_start, _ = cm.start()
        assert ok_start is True
        time.sleep(0.2)

        st = cm.get_status()
        assert st["status"] == "STREAMING"
        assert st["resolution"] == "640x480"
        assert st["camera_name"] == "ESP32-CAM OV2640"

        snap_ok, fname = cm.capture_snapshot(prefix="esp32cam")
        assert snap_ok is True
        saved = (tmp_path / fname).read_bytes()
        assert saved == jpg_bytes
    finally:
        cm.stop()
        server.shutdown()
        server.server_close()
