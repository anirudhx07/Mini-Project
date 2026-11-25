"""Thread-safe Telemetry State Manager with timeout detection and bounded history."""

import math
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional, Tuple

from .calibration import TelemetryCalibration

STATUS_WAITING = "WAITING_FOR_DATA"
STATUS_CONNECTED = "CONNECTED"
STATUS_DISCONNECTED = "DISCONNECTED"
STATUS_INVALID_PACKET = "INVALID_PACKET"
STATUS_SENSOR_ERROR = "SENSOR_ERROR"


def parse_telemetry_packet(raw_payload: str) -> Tuple[Optional[Dict[str, float]], Optional[str]]:
    """Parse and validate 8-field (ax..roll) or 9-field (millis,ax..roll) CSV telemetry."""
    if not raw_payload or not isinstance(raw_payload, str):
        return None, "Empty or non-string payload"

    cleaned = raw_payload.strip()
    parts = [p.strip() for p in cleaned.split(",")]
    if len(parts) not in (8, 9):
        return None, f"Expected 8 or 9 fields, got {len(parts)}"

    try:
        values = [float(p) for p in parts]
    except ValueError:
        return None, "Non-numeric value in packet"

    if any(not math.isfinite(v) for v in values):
        return None, "NaN or Inf value in packet"

    # For 9-field packets, first field is device millis (ignored for sensor calculations)
    sensor_values = values[1:] if len(values) == 9 else values

    return {
        "ax": sensor_values[0],
        "ay": sensor_values[1],
        "az": sensor_values[2],
        "gx": sensor_values[3],
        "gy": sensor_values[4],
        "gz": sensor_values[5],
        "pitch": sensor_values[6],
        "roll": sensor_values[7],
        "field_count": len(values),
    }, None


class TelemetryManager:
    """Maintains latest ESP32/MPU6050 telemetry, bounded history, and connection state."""

    def __init__(
        self,
        timeout_sec: float = 3.0,
        history_size: int = 300,
        event_logger=None,
        socketio=None,
    ):
        self._lock = threading.Lock()
        self.timeout_sec = float(timeout_sec)
        self.history_size = int(history_size)
        self._event_logger = event_logger
        self._socketio = socketio
        self._serial_provider = None
        self._comm_mode_provider = None
        self.calibration = TelemetryCalibration()

        self._demo_mode = False
        self._status = STATUS_WAITING
        self._ever_connected = False
        self._last_packet_mono: Optional[float] = None
        self._last_packet_ts: Optional[str] = None
        self._last_source_ip: Optional[str] = None
        self._last_error: Optional[str] = None

        self._packet_count = 0
        self._invalid_count = 0
        self._rate_window: Deque[float] = deque(maxlen=50)
        self._last_emit_mono = 0.0

        self._latest: Optional[Dict[str, Any]] = None
        self._history: Deque[Dict[str, Any]] = deque(maxlen=self.history_size)

    def set_socketio(self, socketio):
        self._socketio = socketio

    def set_serial_provider(self, serial_provider, comm_mode_provider=None):
        """Attach authoritative serial status and comm_mode providers."""
        self._serial_provider = serial_provider
        self._comm_mode_provider = comm_mode_provider

    def broadcast_state(self):
        """Public helper to broadcast authoritative telemetry + serial state over WebSocket."""
        self._broadcast_state()

    def set_timeout(self, timeout_sec: float):
        with self._lock:
            self.timeout_sec = max(0.5, float(timeout_sec))

    def set_history_size(self, size: int):
        with self._lock:
            size = max(20, min(int(size), 2000))
            self.history_size = size
            old = list(self._history)[-size:]
            self._history = deque(old, maxlen=size)

    def is_demo_mode(self) -> bool:
        with self._lock:
            return self._demo_mode

    def set_demo_mode(self, enabled: bool):
        with self._lock:
            self._demo_mode = bool(enabled)
            self._latest = None
            self._history.clear()
            self._rate_window.clear()
            self._last_packet_mono = None
            self._last_error = None
            self._status = STATUS_WAITING
        if self._event_logger:
            mode_label = "DEMO MODE enabled (simulated telemetry)" if enabled else "REAL HARDWARE MODE active"
            self._event_logger.log("SYSTEM", mode_label, level="WARNING" if enabled else "INFO")

    def ingest_raw_packet(self, raw_payload: str, source_ip: str = "", is_demo: bool = False) -> bool:
        """Validate and store an incoming UDP telemetry packet."""
        with self._lock:
            # Never mix simulated data into real hardware mode or vice-versa
            if is_demo != self._demo_mode:
                return False

        parsed, err = parse_telemetry_packet(raw_payload)
        now_mono = time.monotonic()
        now_iso = datetime.now(timezone.utc).astimezone().strftime("%H:%M:%S.%f")[:-3]

        if err is not None or parsed is None:
            log_err = False
            with self._lock:
                self._invalid_count += 1
                self._last_error = err
                if self._status != STATUS_INVALID_PACKET:
                    self._status = STATUS_INVALID_PACKET
                    log_err = True
            if log_err and self._event_logger:
                snippet = raw_payload.strip()[:80]
                self._event_logger.log(
                    "ESP32",
                    f"Malformed telemetry packet from {source_ip or 'unknown'}: {err} | raw='{snippet}'",
                    level="WARNING",
                )
            return False

        cal = self.calibration.apply(parsed["pitch"], parsed["roll"])
        sample = {
            "timestamp": now_iso,
            "ax": round(parsed["ax"], 3),
            "ay": round(parsed["ay"], 3),
            "az": round(parsed["az"], 3),
            "gx": round(parsed["gx"], 3),
            "gy": round(parsed["gy"], 3),
            "gz": round(parsed["gz"], 3),
            "yaw_rate": round(parsed["gz"], 3),  # MPU6050 Z-axis angular velocity (deg/s), NOT absolute yaw
            "pitch": cal["pitch"],
            "roll": cal["roll"],
            "raw_pitch": round(parsed["pitch"], 3),
            "raw_roll": round(parsed["roll"], 3),
            "is_demo": is_demo,
        }

        became_connected = False
        should_emit = False
        with self._lock:
            if self._status != STATUS_CONNECTED:
                became_connected = True
            self._status = STATUS_CONNECTED
            self._ever_connected = True
            self._last_packet_mono = now_mono
            self._last_packet_ts = now_iso
            self._last_source_ip = source_ip or self._last_source_ip
            self._last_error = None
            self._packet_count += 1
            self._rate_window.append(now_mono)
            self._latest = sample
            self._history.append(sample)

            # Throttle WebSocket broadcasts to ~20 Hz max so UI & network stay responsive
            if now_mono - self._last_emit_mono >= 0.05:
                self._last_emit_mono = now_mono
                should_emit = True

        if became_connected and self._event_logger:
            src_desc = "DEMO SIMULATOR" if is_demo else f"ESP32 ({source_ip or 'UDP'})"
            self._event_logger.log(
                "ESP32",
                f"{src_desc} valid MPU6050 telemetry received ({int(parsed['field_count'])}-field CSV)",
                level="INFO",
            )

        if should_emit:
            self._broadcast_state()
        return True

    def check_timeout(self) -> str:
        """Check whether ESP32 has timed out (no packet for timeout_sec)."""
        became_disconnected = False
        with self._lock:
            if self._last_packet_mono is not None:
                elapsed = time.monotonic() - self._last_packet_mono
                if elapsed > self.timeout_sec and self._status in (STATUS_CONNECTED, STATUS_INVALID_PACKET):
                    self._status = STATUS_DISCONNECTED
                    became_disconnected = True
            status_now = self._status

        if became_disconnected:
            if self._event_logger:
                self._event_logger.log(
                    "ESP32",
                    f"ESP32 telemetry timeout (no packets for {self.timeout_sec:.1f}s)",
                    level="WARNING",
                )
            self._broadcast_state()
        return status_now

    def mark_disconnected(self, reason: str = ""):
        """Immediately mark ESP32 link disconnected (e.g., USB cable unplugged or port closed)."""
        with self._lock:
            self._status = STATUS_DISCONNECTED
            self._rate_window.clear()
            if reason:
                self._last_error = reason
        self._broadcast_state()

    def mark_sensor_error(self, reason: str = "MPU6050 sensor initialization or read error"):
        """Mark sensor error state without claiming MPU6050 is ONLINE."""
        with self._lock:
            self._status = STATUS_SENSOR_ERROR
            self._rate_window.clear()
            self._last_error = reason
        self._broadcast_state()

    def _compute_rate_hz(self) -> float:
        if len(self._rate_window) < 2:
            return 0.0
        span = self._rate_window[-1] - self._rate_window[0]
        if span <= 0:
            return 0.0
        return round((len(self._rate_window) - 1) / span, 1)

    def get_state(self) -> Dict[str, Any]:
        """Return thread-safe snapshot of telemetry state."""
        self.check_timeout()
        with self._lock:
            age_sec = None
            if self._last_packet_mono is not None:
                age_sec = round(time.monotonic() - self._last_packet_mono, 2)
            mpu_status = "ONLINE" if self._status == STATUS_CONNECTED else (
                "SENSOR_ERROR" if self._status == STATUS_SENSOR_ERROR else (
                    "BAD_PACKET" if self._status == STATUS_INVALID_PACKET else (
                        "TIMEOUT" if self._status == STATUS_DISCONNECTED else "WAITING"
                    )
                )
            )
            payload = {
                "status": self._status,
                "mpu6050_status": mpu_status,
                "demo_mode": self._demo_mode,
                "source_ip": self._last_source_ip,
                "last_packet_ts": self._last_packet_ts,
                "packet_age_sec": age_sec,
                "packet_count": self._packet_count,
                "invalid_count": self._invalid_count,
                "rate_hz": self._compute_rate_hz() if self._status == STATUS_CONNECTED else 0.0,
                "last_error": self._last_error,
                "calibration": self.calibration.get_offsets(),
                "data": dict(self._latest) if self._latest is not None else None,
            }

        if self._comm_mode_provider is not None:
            try:
                payload["comm_mode"] = self._comm_mode_provider()
            except Exception:
                pass
        if self._serial_provider is not None:
            try:
                ser = self._serial_provider()
                payload["serial"] = {
                    "connected": bool(ser.get("connected")),
                    "running": bool(ser.get("running")),
                    "port": ser.get("port"),
                    "baudrate": ser.get("baudrate"),
                    "baud_rate": ser.get("baudrate"),
                    "last_packet_ts": ser.get("last_packet_ts"),
                    "last_received_packet": ser.get("last_packet_ts"),
                    "connection_status": "CONNECTED" if ser.get("connected") else "DISCONNECTED",
                    "last_error": ser.get("last_error", ""),
                    "serial_error": ser.get("last_error", ""),
                }
            except Exception:
                pass
        return payload

    def get_history(self, limit: int = 120) -> List[Dict[str, Any]]:
        """Return bounded historical telemetry samples."""
        with self._lock:
            lim = max(1, min(int(limit), self.history_size))
            return list(self._history)[-lim:]

    def _broadcast_state(self):
        if self._socketio is not None:
            try:
                self._socketio.emit("telemetry_update", self.get_state())
            except Exception:
                pass
