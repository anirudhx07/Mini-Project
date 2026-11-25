"""Tests for UDP telemetry parsing, timeout detection, mode isolation, and UDP socket reception."""

import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.telemetry.telemetry_manager import (
    STATUS_CONNECTED,
    STATUS_DISCONNECTED,
    STATUS_INVALID_PACKET,
    STATUS_WAITING,
    TelemetryManager,
    parse_telemetry_packet,
)
from backend.telemetry.udp_receiver import UDPTelemetryReceiver


def test_parse_valid_packet():
    parsed, err = parse_telemetry_packet("0.12,-0.34,9.81,1.5,-2.0,0.4,3.2,-1.1")
    assert err is None
    assert parsed is not None
    assert parsed["az"] == 9.81
    assert parsed["pitch"] == 3.2
    assert parsed["roll"] == -1.1


def test_parse_invalid_packets():
    for bad in ["", "1,2,3", "1,2,3,4,5,6,7,abc", "nan,0,0,0,0,0,0,0", "1,2,3,4,5,6,7,8,9"]:
        parsed, err = parse_telemetry_packet(bad)
        assert parsed is None
        assert err is not None


def test_invalid_packet_updates_state():
    tm = TelemetryManager(timeout_sec=3.0)
    assert tm.get_state()["status"] == STATUS_WAITING
    ok = tm.ingest_raw_packet("bad,packet,data", source_ip="192.168.1.50", is_demo=False)
    assert ok is False
    st = tm.get_state()
    assert st["status"] == STATUS_INVALID_PACKET
    assert st["invalid_count"] == 1


def test_esp32_timeout_detection():
    tm = TelemetryManager(timeout_sec=0.25)
    ok = tm.ingest_raw_packet("0,0,9.81,0,0,0,1.0,2.0", source_ip="192.168.1.42", is_demo=False)
    assert ok is True
    assert tm.get_state()["status"] == STATUS_CONNECTED

    time.sleep(0.35)
    st = tm.get_state()
    assert st["status"] == STATUS_DISCONNECTED
    assert st["mpu6050_status"] == "TIMEOUT"


def test_real_vs_demo_mode_isolation():
    tm = TelemetryManager()
    assert tm.is_demo_mode() is False
    # Demo packets must be rejected in Real Hardware Mode
    assert tm.ingest_raw_packet("0,0,9.8,0,0,0,0,0", is_demo=True) is False
    assert tm.get_state()["packet_count"] == 0


def test_udp_receiver_loopback():
    tm = TelemetryManager(timeout_sec=2.0)
    recv = UDPTelemetryReceiver(tm, host="127.0.0.1", port=0)
    # Bind ephemeral port for safe isolated test
    recv._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    recv._sock.bind(("127.0.0.1", 0))
    recv._sock.settimeout(0.3)
    port = recv._sock.getsockname()[1]
    recv._running = True
    import threading
    recv._thread = threading.Thread(target=recv._listen_loop, daemon=True)
    recv._thread.start()

    try:
        sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sender.sendto(b"0.1,0.2,9.8,1.0,2.0,3.0,4.5,-2.5", ("127.0.0.1", port))
        sender.close()
        time.sleep(0.15)
        st = tm.get_state()
        assert st["status"] == STATUS_CONNECTED
        assert st["data"]["pitch"] == 4.5
        assert st["data"]["yaw_rate"] == 3.0
    finally:
        recv.stop()
