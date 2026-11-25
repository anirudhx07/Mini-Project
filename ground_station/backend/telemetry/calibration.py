"""Telemetry zero-offset calibration helper for MPU6050 breadboard testing."""

import threading
from typing import Dict


class TelemetryCalibration:
    """Stores optional software pitch/roll trim offsets without altering raw sensor logs."""

    def __init__(self):
        self._lock = threading.Lock()
        self.pitch_offset = 0.0
        self.roll_offset = 0.0

    def set_zero(self, current_pitch: float, current_roll: float):
        with self._lock:
            self.pitch_offset = float(current_pitch)
            self.roll_offset = float(current_roll)

    def reset(self):
        with self._lock:
            self.pitch_offset = 0.0
            self.roll_offset = 0.0

    def apply(self, pitch: float, roll: float) -> Dict[str, float]:
        with self._lock:
            return {
                "pitch": round(pitch - self.pitch_offset, 3),
                "roll": round(roll - self.roll_offset, 3),
            }

    def get_offsets(self) -> Dict[str, float]:
        with self._lock:
            return {
                "pitch_offset": round(self.pitch_offset, 3),
                "roll_offset": round(self.roll_offset, 3),
            }
