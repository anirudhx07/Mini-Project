"""Thread-safe ring frame buffer with diagnostic dropped frame accounting."""

import threading
import time
from typing import Optional, Tuple
import numpy as np


class FrameBuffer:
    """Thread-safe fixed-capacity FIFO frame buffer for video ingestion."""

    def __init__(self, maxsize: int = 15):
        self.maxsize = maxsize
        self._buffer = []
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self.total_received = 0
        self.total_dropped = 0
        self.last_ingest_time = 0.0

    def put(self, frame: np.ndarray, timestamp: Optional[float] = None) -> bool:
        """Insert a frame into the buffer. Drops oldest frame if capacity exceeded."""
        if timestamp is None:
            timestamp = time.time()

        with self._lock:
            self.total_received += 1
            self.last_ingest_time = timestamp

            if len(self._buffer) >= self.maxsize:
                # Drop oldest frame to ensure real-time responsiveness
                self._buffer.pop(0)
                self.total_dropped += 1
                dropped = True
            else:
                dropped = False

            self._buffer.append((frame, timestamp))
            self._not_empty.notify()
            return dropped

    def get(self, timeout: Optional[float] = 1.0) -> Tuple[Optional[np.ndarray], float]:
        """Retrieve the oldest frame. Blocks up to timeout seconds if empty."""
        with self._not_empty:
            if not self._buffer:
                if not self._not_empty.wait(timeout):
                    return None, 0.0
                if not self._buffer:
                    return None, 0.0

            frame, ts = self._buffer.pop(0)
            return frame, ts

    def drop_rate(self) -> float:
        """Calculate historical frame drop percentage."""
        with self._lock:
            if self.total_received == 0:
                return 0.0
            return (self.total_dropped / self.total_received) * 100.0

    def clear(self):
        """Purge all buffered frames."""
        with self._lock:
            self._buffer.clear()
