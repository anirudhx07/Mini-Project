"""Tests for Flask REST APIs, AI/Tracking unavailability handling, Camouflage fallback, and WebSockets."""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app, socketio
from config import Config


class TestConfig(Config):
    TESTING = True
    YOLO_MODEL_PATH = str(Path(__file__).resolve().parent / "nonexistent_yolo.pt")
    DATABASE_PATH = Path(__file__).resolve().parent / "tmp_test_logs.db"
    CAPTURES_DIR = Path(__file__).resolve().parent / "tmp_captures"


def _make_client():
    app = create_app(start_background=False, config_cls=TestConfig)
    return app, app.test_client()


def test_telemetry_and_status_api():
    app, client = _make_client()
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["app"] == "COCKPIT"
    assert data["comm_mode"] == "USB_SERIAL"
    assert data["telemetry"]["demo_mode"] is False

    resp_tel = client.get("/api/telemetry")
    assert resp_tel.status_code == 200
    assert resp_tel.get_json()["telemetry"]["status"] == "WAITING_FOR_DATA"


def test_serial_api_endpoints():
    app, client = _make_client()
    r_ports = client.get("/api/serial/ports")
    assert r_ports.status_code == 200
    assert "ports" in r_ports.get_json()

    r_stat = client.get("/api/serial/status")
    assert r_stat.status_code == 200
    assert r_stat.get_json()["serial"]["connected"] is False

    # Missing port should return 400
    r_bad = client.post("/api/serial/connect", json={"port": "", "baudrate": 115200})
    assert r_bad.status_code == 400

    # Unavailable port should return 409
    r_unavail = client.post("/api/serial/connect", json={"port": "COM250", "baudrate": 115200})
    assert r_unavail.status_code == 409

    r_disc = client.post("/api/serial/disconnect")
    assert r_disc.status_code == 200


def test_ai_model_unavailable_handling():
    app, client = _make_client()
    resp = client.post("/api/detection/start", json={})
    assert resp.status_code == 409
    data = resp.get_json()
    assert data["ok"] is False
    assert data["detection"]["model_loaded"] is False


def test_tracking_unavailable_handling():
    app, client = _make_client()
    resp = client.post("/api/tracking/start", json={})
    assert resp.status_code == 409
    data = resp.get_json()
    assert data["ok"] is False
    assert data["tracking"]["running"] is False


def test_camouflage_analysis_baseline_and_no_frame():
    app, client = _make_client()
    # Without active camera, returns 409 cleanly
    resp = client.post("/api/camouflage/analyze", json={"sensitivity": 0.6})
    assert resp.status_code == 409

    # Direct baseline analyzer test on synthetic numpy frame
    camo = app.extensions["camouflage_analyzer"]
    sample = np.zeros((120, 160, 3), dtype=np.uint8)
    sample[40:80, 50:100] = (40, 180, 90)
    res = camo.analyze_frame(sample, sensitivity=0.6, save_result=False)
    assert res["analysis_type"] == "BASELINE_VISUAL_ANALYSIS"
    assert res["trained_model_status"] == "MODEL_NOT_CONFIGURED"
    assert "analyzed_b64" in res


def test_websocket_connection():
    app, _ = _make_client()
    ws_client = socketio.test_client(app)
    assert ws_client.is_connected()
    received = ws_client.get_received()
    tel_pkts = [pkt for pkt in received if pkt["name"] == "telemetry_update"]
    assert len(tel_pkts) >= 1
    payload = tel_pkts[0]["args"][0]
    assert "serial" in payload
    assert payload["serial"]["connected"] is False
    assert payload["serial"]["connection_status"] == "DISCONNECTED"
    ws_client.disconnect()
