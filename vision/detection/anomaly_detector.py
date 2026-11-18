"""Statistical background anomaly detection using local Mahalanobis / Gaussian modeling."""

import cv2
import numpy as np
from typing import Dict, Any


class AnomalyDetector:
    """Evaluates pixel residual anomalies relative to surrounding terrain distribution."""

    def __init__(self, history_size: int = 10, variance_thresh: float = 16.0):
        self.subtractor = cv2.createBackgroundSubtractorMOG2(
            history=history_size,
            varThreshold=variance_thresh,
            detectShadows=False
        )

    def detect(self, frame: np.ndarray) -> Dict[str, Any]:
        """Compute anomaly mask using adaptive gaussian mixture model."""
        fg_mask = self.subtractor.apply(frame)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        cleaned = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections = []
        for c in contours:
            if cv2.contourArea(c) > 100:
                x, y, w, h = cv2.boundingRect(c)
                detections.append([x, y, w, h])

        return {
            "mask": cleaned,
            "anomaly_count": len(detections),
            "bounding_boxes": detections
        }
