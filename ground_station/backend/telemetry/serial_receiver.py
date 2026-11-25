"""USB Serial Telemetry Receiver for ESP32 DevKit V1 (Silicon Labs CP210x) using pyserial."""

import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import serial
import serial.tools.list_ports

from .telemetry_manager import TelemetryManager

CP210X_VID = 0x10C4  # 4292
CP210X_PIDS = {0xEA60, 0xEA70, 0xEA71}
ALLOWED_BAUDRATES = (9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600)


def list_serial_ports() -> List[Dict[str, Any]]:
    """Enumerate available serial COM ports and flag Silicon Labs CP210x devices."""
    ports_out: List[Dict[str, Any]] = []
    for p in serial.tools.list_ports.comports():
        desc = p.description or ""
        hwid = p.hwid or ""
        is_cp210x = (
            (p.vid == CP210X_VID and (p.pid in CP210X_PIDS or p.pid is not None))
            or ("CP210" in desc.upper())
            or ("10C4:EA60" in hwid.upper())
        )
        ports_out.append({
            "device": p.device,
            "description": desc,
            "hwid": hwid,
            "vid": f"0x{p.vid:04X}" if p.vid is not None else None,
            "pid": f"0x{p.pid:04X}" if p.pid is not None else None,
            "is_cp210x": is_cp210x,
            "recommended": is_cp210x,
        })

    # Sort recommended CP210x devices first, then alphabetically by port name
    ports_out.sort(key=lambda item: (not item["is_cp210x"], item["device"]))
    return ports_out


class SerialTelemetryReceiver:
    """Reads newline-terminated CSV MPU6050 telemetry from ESP32 over USB Serial."""

    def __init__(
        self,
        telemetry_manager: TelemetryManager,
        default_baudrate: int = 115200,
        event_logger=None,
    ):
        self.telemetry_manager = telemetry_manager
        self._event_logger = event_logger

        self._lock = threading.Lock()
        self._serial: Optional[serial.Serial] = None
        self._port: str = ""
        self._baudrate: int = int(default_baudrate)
        self._running = False
        self._connected = False
        self._last_error: str = ""
        self._thread: Optional[threading.Thread] = None
        self._watchdog_thread: Optional[threading.Thread] = None

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def is_connected(self) -> bool:
        with self._lock:
            return self._connected and self._serial is not None and self._serial.is_open

    def connect(self, port: str, baudrate: int = 115200) -> Tuple[bool, str]:
        """Validate port & baudrate, open COM port exclusively, and start reader thread."""
        port_clean = (port or "").strip()
        if not port_clean:
            return False, "Serial COM port is required"

        try:
            baud_int = int(baudrate)
        except (TypeError, ValueError):
            return False, "Invalid baud rate value"

        if baud_int not in ALLOWED_BAUDRATES:
            return False, f"Unsupported baud rate {baud_int}. Allowed: {', '.join(map(str, ALLOWED_BAUDRATES))}"

        available = {p["device"].upper(): p for p in list_serial_ports()}
        if port_clean.upper() not in available:
            msg = f"COM port '{port_clean}' is not currently available"
            with self._lock:
                self._last_error = msg
            return False, msg

        # If already connected to a port, close cleanly first to prevent duplicate readers
        if self.is_running() or self.is_connected():
            self.disconnect()

        try:
            ser = serial.Serial(
                port=port_clean,
                baudrate=baud_int,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.5,
            )
            try:
                ser.reset_input_buffer()
            except Exception:
                pass
        except serial.SerialException as exc:
            err_str = str(exc)
            if "PermissionError" in err_str or "Access is denied" in err_str:
                msg = f"Access denied on {port_clean}. Close Arduino Serial Monitor or other apps using {port_clean}."
            else:
                msg = f"Failed to open {port_clean}: {err_str}"
            with self._lock:
                self._connected = False
                self._last_error = msg
            if self._event_logger:
                self._event_logger.log("ESP32", msg, level="ERROR")
            return False, msg
        except Exception as exc:
            msg = f"Unexpected error opening {port_clean}: {exc}"
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
            self._thread = threading.Thread(target=self._read_loop, name="USBSerialReader", daemon=True)
            self._watchdog_thread = threading.Thread(target=self._watchdog_loop, name="USBSerialWatchdog", daemon=True)
            self._thread.start()
            self._watchdog_thread.start()

        msg = f"USB Serial opened on {port_clean} @ {baud_int} baud (waiting for telemetry packets)"
        if self._event_logger:
            self._event_logger.log("ESP32", msg, level="INFO")
        return True, msg

    def disconnect(self):
        """Stop background reader and release COM port cleanly."""
        with self._lock:
            was_open = self._connected or self._running or (self._serial is not None)
            prev_port = self._port
            self._running = False
            self._connected = False
            ser = self._serial
            self._serial = None
            t_read = self._thread
            t_watch = self._watchdog_thread
            self._thread = None
            self._watchdog_thread = None

        if ser is not None:
            try:
                if ser.is_open:
                    ser.close()
            except Exception:
                pass

        if t_read and t_read.is_alive() and threading.current_thread() != t_read:
            t_read.join(timeout=1.5)
        if t_watch and t_watch.is_alive() and threading.current_thread() != t_watch:
            t_watch.join(timeout=1.5)

        if was_open:
            self.telemetry_manager.mark_disconnected(f"USB Serial {prev_port} disconnected")
            if self._event_logger and prev_port:
                self._event_logger.log("ESP32", f"USB Serial disconnected and released ({prev_port})", level="INFO")

    def _read_loop(self):
        while True:
            with self._lock:
                if not self._running or self._serial is None:
                    break
                ser = self._serial
                port_name = self._port

            try:
                raw_bytes = ser.readline()
            except (serial.SerialException, OSError) as exc:
                msg = f"Serial connection lost on {port_name}: {exc}"
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
                self.telemetry_manager.mark_disconnected(msg)
                if self._event_logger:
                    self._event_logger.log("ESP32", msg, level="ERROR")
                break
            except Exception:
                continue

            if not raw_bytes:
                continue

            line = raw_bytes.decode("utf-8", errors="replace").strip()
            if not line:
                continue

            self.telemetry_manager.ingest_raw_packet(
                line,
                source_ip=f"USB:{port_name}",
                is_demo=False,
            )

    def _watchdog_loop(self):
        while self.is_running():
            self.telemetry_manager.check_timeout()
            time.sleep(0.5)

    def get_status(self) -> Dict[str, Any]:
        tm_state = self.telemetry_manager.get_state()
        with self._lock:
            return {
                "connected": self._connected and self._serial is not None and self._serial.is_open,
                "running": self._running,
                "port": self._port or None,
                "baudrate": self._baudrate,
                "last_packet_ts": tm_state.get("last_packet_ts"),
                "last_error": self._last_error,
                "allowed_baudrates": list(ALLOWED_BAUDRATES),
            }
