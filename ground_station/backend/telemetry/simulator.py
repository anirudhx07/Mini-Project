"""Explicitly Opt-In Telemetry Simulator for Software Testing (Disabled by Default)."""

import math
import threading
import time
from typing import Optional

from .telemetry_manager import TelemetryManager


class TelemetrySimulator:
    """Generates labeled synthetic MPU6050 packets ONLY when DEMO MODE is explicitly enabled."""

    def __init__(self, telemetry_manager: TelemetryManager, rate_hz: float = 20.0):
        self.telemetry_manager = telemetry_manager
        self.rate_hz = rate_hz
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def is_running(self) -> bool:
        return self._running

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="DemoTelemetrySimulator", daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)

    def _loop(self):
        t = 0.0
        interval = 1.0 / max(1.0, self.rate_hz)
        while self._running:
            if self.telemetry_manager.is_demo_mode():
                pitch = 6.5 * math.sin(t * 0.9) + 1.2 * math.cos(t * 2.1)
                roll = 8.0 * math.cos(t * 0.7) + 1.0 * math.sin(t * 1.7)
                ax = 9.81 * math.sin(math.radians(pitch))
                ay = 9.81 * math.sin(math.radians(roll))
                az = 9.81 * math.cos(math.radians(pitch)) * math.cos(math.radians(roll))
                gx = 12.0 * math.cos(t * 1.1)
                gy = -9.5 * math.sin(t * 0.8)
                gz = 4.2 * math.sin(t * 0.5)
                payload = f"{ax:.3f},{ay:.3f},{az:.3f},{gx:.3f},{gy:.3f},{gz:.3f},{pitch:.3f},{roll:.3f}"
                self.telemetry_manager.ingest_raw_packet(payload, source_ip="DEMO-SIM", is_demo=True)
                t += interval
            time.sleep(interval)
