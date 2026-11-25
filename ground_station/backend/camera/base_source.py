"""Abstract Base Interface for Modular Camera Sources."""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
import numpy as np


class CameraSource(ABC):
    """Base contract for any camera adapter (Laptop Webcam, ESP32-CAM, etc.)."""

    @abstractmethod
    def open(self) -> Tuple[bool, str]:
        """Open camera device or stream. Returns (success, message)."""

    @abstractmethod
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read a single BGR frame."""

    @abstractmethod
    def release(self):
        """Release underlying hardware/network resources."""

    @abstractmethod
    def is_opened(self) -> bool:
        """Check if source is currently active."""

    @abstractmethod
    def source_name(self) -> str:
        """Human-readable source identifier."""
