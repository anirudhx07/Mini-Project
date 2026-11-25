"""Tests for USB Serial telemetry parsing, CP210x detection, unavailable ports, malformed data, disconnect/reconnect."""

import sys
import time
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.telemetry import serial_receiver as sr_mod
from backend.telemetry.serial_receiver import SerialTelemetryReceiver, list_serial_ports
from backend.telemetry.telemetry_manager import (
    STATUS_CONNECTED,
    STATUS_DISCONNECTED,
    STATUS_INVALID_PACKET,
    TelemetryManager,
)


class _FakeSerialPort:
    """In-memory fake pyserial.Serial stream for deterministic unit testing."""

    def __init__(self, lines):
        self._lines = list(lines)
        self.is_open = True

    def reset_input_buffer(self):
        pass

    def readline(self):
        if not self.is_open:
            raise OSError("Port closed")
        if self._lines:
            return self._lines.pop(0)
        time.sleep(0.02)
        return b""

    def close(self):
        self.is_open = False


def test_list_serial_ports_identifies_cp210x(monkeypatch):
    fake_ports = [
        SimpleNamespace(device="COM3", description="Bluetooth Link", hwid="BTHENUM", vid=None, pid=None),
        SimpleNamespace(device="COM5", description="Silicon Labs CP210x USB to UART Bridge (COM5)", hwid="USB VID:PID=10C4:EA60", vid=0x10C4, pid=0xEA60),
    ]
    monkeypatch.setattr(sr_mod.serial.tools.list_ports, "comports", lambda: fake_ports)
    ports = list_serial_ports()
    assert len(ports) == 2
    assert ports[0]["device"] == "COM5"
    assert ports[0]["is_cp210x"] is True
    assert ports[1]["is_cp210x"] is False


def test_serial_unavailable_port_fails_gracefully(monkeypatch):
    monkeypatch.setattr(sr_mod, "list_serial_ports", lambda: [])
    tm = TelemetryManager()
    receiver = SerialTelemetryReceiver(tm)
    ok, msg = receiver.connect("COM99", 115200)
    assert ok is False
    assert "not currently available" in msg.lower()
    assert receiver.is_connected() is False


def test_serial_valid_malformed_disconnect_and_reconnect(monkeypatch):
    fake_port_list = [{"device": "COM5", "description": "CP210x", "is_cp210x": True}]
    monkeypatch.setattr(sr_mod, "list_serial_ports", lambda: fake_port_list)

    streams = [
        _FakeSerialPort([
            b"0.12,0.25,9.72,1.20,0.45,0.15,2.40,-1.20\n",
            b"DEBUG: ignoring malformed line\n",
        ]),
        _FakeSerialPort([
            b"0.00,0.00,9.81,0.00,0.00,0.50,1.00,-0.50\n",
        ]),
    ]

    def fake_serial_factory(*args, **kwargs):
        return streams.pop(0)

    monkeypatch.setattr(sr_mod.serial, "Serial", fake_serial_factory)

    tm = TelemetryManager(timeout_sec=3.0)
    receiver = SerialTelemetryReceiver(tm)

    # Connect and read valid + malformed CSV
    ok, _ = receiver.connect("COM5", 115200)
    assert ok is True
    time.sleep(0.15)
    st = tm.get_state()
    assert st["data"]["pitch"] == 2.40
    assert st["data"]["roll"] == -1.20
    assert st["packet_count"] >= 1
    assert st["invalid_count"] >= 1
    assert st["status"] == STATUS_INVALID_PACKET or st["status"] == STATUS_CONNECTED

    # Disconnect releases port and marks disconnected
    receiver.disconnect()
    assert receiver.is_connected() is False
    assert tm.get_state()["status"] == STATUS_DISCONNECTED

    # Reconnect safely with second stream
    ok2, _ = receiver.connect("COM5", 115200)
    assert ok2 is True
    time.sleep(0.15)
    st2 = tm.get_state()
    assert st2["status"] == STATUS_CONNECTED
    assert st2["data"]["pitch"] == 1.00
    receiver.disconnect()
