"""Independent USB Serial Diagnostics Monitor for ESP32-CAM (does not control Wi-Fi stream status)."""

import re
import threading
import time
from typing import Any, Dict, Optional, Tuple

import serial

from backend.telemetry.serial_receiver import ALLOWED_BAUDRATES, list_serial_ports


class CamSerialMonitor:
    """Optional USB serial connection for ESP32-CAM diagnostics & IP discovery."""

    def __init__(self, default_baudrate: int = 115200, event_logger=None):
        self._event_logger = event_logger
        self._lock = threading.Lock()
        self._serial: Optional[serial.Serial] = None
        self._port: str = ""
        self._baudrate: int = int(default_baudrate)
        self._running = False
        self._connected = False
        self._last_error: str = ""
        self._last_line: str = ""
        self._detected_ip: str = ""
        self._thread: Optional[threading.Thread] = None

    def connect(self, port: str, baudrate: int = 115200) -> Tuple[bool, str]:
        port_clean = (port or "").strip()
        if not port_clean:
            return False, "COM port selection is required"

        try:
            baud_int = int(baudrate)
        except (TypeError, ValueError):
            return False, "Invalid baud rate"

        if baud_int not in ALLOWED_BAUDRATES:
            return False, f"Unsupported baud rate {baud_int}"

        available = {p["device"].upper() for p in list_serial_ports()}
        if port_clean.upper() not in available:
            msg = f"COM port '{port_clean}' is not available"
            with self._lock:
                self._last_error = msg
            return False, msg

        if self._running or self._connected:
            self.disconnect()

        try:
            ser = serial.Serial()
            ser.port = port_clean
            ser.baudrate = baud_int
            ser.timeout = 0.5
            ser.dtr = False
            ser.rts = False
            ser.open()
        except serial.SerialException as exc:
            err_str = str(exc)
            if "PermissionError" in err_str or "Access is denied" in err_str:
                msg = f"Access denied on {port_clean}. Close Arduino Serial Monitor or other tools using {port_clean}."
            else:
                msg = f"Failed to open {port_clean}: {err_str}"
            with self._lock:
                self._connected = False
                self._last_error = msg
            if self._event_logger:
                self._event_logger.log("CAMERA", msg, level="ERROR")
            return False, msg
        except Exception as exc:
            msg = f"Unexpected serial error on {port_clean}: {exc}"
            with self._lock:
                self._connected = False
                self._last_error = msg
            return False, msg

        with self._lock:
            self._serial = ser
            self._port = port_clean
            self._baudrate = baud_int
            self._running = True
            self._connected = True
            self._last_error = ""
            self._thread = threading.Thread(target=self._read_loop, name="CamUSBSerialMonitor", daemon=True)
            self._thread.start()

        msg = f"ESP32-CAM USB serial connected on {port_clean} @ {baud_int}"
        if self._event_logger:
            self._event_logger.log("CAMERA", msg, level="INFO")
        return True, msg

    def disconnect(self):
        with self._lock:
            was_open = self._connected or self._running or (self._serial is not None)
            prev_port = self._port
            self._running = False
            self._connected = False
            ser = self._serial
            self._serial = None
            t_read = self._thread
            self._thread = None

        if ser is not None:
            try:
                if ser.is_open:
                    ser.close()
            except Exception:
                pass
        if t_read and t_read.is_alive() and threading.current_thread() != t_read:
            t_read.join(timeout=1.5)

        if was_open and self._event_logger and prev_port:
            self._event_logger.log("CAMERA", f"ESP32-CAM USB serial disconnected ({prev_port})", level="INFO")

    def _read_loop(self):
        rx_buf = bytearray()
        while True:
            with self._lock:
                if not self._running or self._serial is None:
                    break
                ser = self._serial
                port_name = self._port

            try:
                waiting = getattr(ser, "in_waiting", 0)
                chunk = ser.read(waiting if waiting > 0 else 1)
            except (serial.SerialException, OSError) as exc:
                msg = f"ESP32-CAM USB disconnected on {port_name}: {exc}"
                with self._lock:
                    self._last_error = msg
                    self._running = False
                    self._connected = False
                    if self._serial is not None:
                        try:
                            self._serial.close()
                        except Exception:
                            pass
                        self._serial = None
                if self._event_logger:
                    self._event_logger.log("CAMERA", msg, level="WARNING")
                break
            except Exception:
                continue

            if not chunk:
                continue

            rx_buf.extend(chunk)
            if len(rx_buf) > 4096 and b"\n" not in rx_buf:
                rx_buf.clear()
                continue

            while b"\n" in rx_buf:
                raw_line, _, rest = rx_buf.partition(b"\n")
                rx_buf = bytearray(rest)
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                ip_match = re.search(r"http://(\d{1,3}(?:\.\d{1,3}){3})", line)
                with self._lock:
                    self._last_line = line[:200]
                    if ip_match:
                        self._detected_ip = ip_match.group(1)

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            is_conn = self._connected and self._serial is not None and self._serial.is_open
            return {
                "connected": is_conn,
                "running": self._running,
                "port": self._port if is_conn else None,
                "baudrate": self._baudrate,
                "last_line": self._last_line,
                "detected_ip": self._detected_ip or None,
                "last_error": self._last_error,
            }
