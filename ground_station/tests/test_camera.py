"""Tests for Camera Abstraction, Initialization, Unavailability Handling, and Shutdown."""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.camera.base_source import CameraSource
from backend.camera.camera_manager import CameraManager
from backend.camera.esp32cam_source import ESP32CamSource


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
    assert cm.get_status()["status"] == "STOPPED"
    assert fake.is_opened() is False


def test_camera_unavailable_handling(tmp_path):
    cm = CameraManager(captures_dir=tmp_path)
    cm._build_source = lambda: _FakeCameraSource(should_open=False)
    ok, msg = cm.start()
    assert ok is False
    assert cm.get_status()["status"] == "UNAVAILABLE"
    assert cm.get_status()["running"] is False
