"""Non-blocking Background UDP Receiver for ESP32 MPU6050 Telemetry."""

import socket
import threading
from typing import Optional

from .telemetry_manager import TelemetryManager


class UDPTelemetryReceiver:
    """Listens on 0.0.0.0:4210 (configurable) for ESP32 UDP telemetry packets."""

    def __init__(
        self,
        telemetry_manager: TelemetryManager,
        host: str = "0.0.0.0",
        port: int = 4210,
        event_logger=None,
    ):
        self.telemetry_manager = telemetry_manager
        self.host = host
        self.port = int(port)
        self._event_logger = event_logger

        self._sock: Optional[socket.socket] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._watchdog_thread: Optional[threading.Thread] = None

    def is_running(self) -> bool:
        return self._running

    def start(self):
        """Bind UDP socket and launch non-blocking listener and timeout watchdog threads."""
        if self._running:
            return
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.settimeout(0.5)

        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, name="UDPTelemetryListener", daemon=True)
        self._thread.start()

        self._watchdog_thread = threading.Thread(target=self._watchdog_loop, name="ESP32TimeoutWatchdog", daemon=True)
        self._watchdog_thread.start()

        if self._event_logger:
            self._event_logger.log("SYSTEM", f"UDP telemetry listener bound on {self.host}:{self.port}", level="INFO")

    def stop(self):
        """Safely shut down listener thread and release UDP socket."""
        self._running = False
        if self._sock is not None:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)
        if self._watchdog_thread and self._watchdog_thread.is_alive():
            self._watchdog_thread.join(timeout=1.5)

    def restart(self, new_port: int):
        """Rebind UDP listener to a new port."""
        self.stop()
        self.port = int(new_port)
        self.start()

    def _listen_loop(self):
        while self._running and self._sock is not None:
            try:
                data, addr = self._sock.recvfrom(1024)
                payload = data.decode("utf-8", errors="replace")
                self.telemetry_manager.ingest_raw_packet(payload, source_ip=addr[0], is_demo=False)
            except socket.timeout:
                continue
            except OSError:
                break
            except Exception:
                continue

    def _watchdog_loop(self):
        while self._running:
            self.telemetry_manager.check_timeout()
            threading.Event().wait(0.5)
