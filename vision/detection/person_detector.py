"""Plan B (Fallback): Pretrained human detector with multi-version OpenCV compatibility."""

import cv2
import numpy as np
from typing import Dict, Any, List


class PersonDetector:
    """Documented Plan B fallback: Detector for human targets in camera feed."""

    def __init__(self, hit_threshold: float = 0.0, win_stride: tuple[int, int] = (8, 8)):
        self.hit_threshold = hit_threshold
        self.win_stride = win_stride
        self._has_hog = hasattr(cv2, 'HOGDescriptor')
        if self._has_hog:
            try:
                self.hog = cv2.HOGDescriptor()
                self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            except Exception:
                self._has_hog = False

    def detect(self, frame: np.ndarray) -> Dict[str, Any]:
        """Detect human targets and return bounding boxes and confidence scores."""
        if self._has_hog:
            return self._detect_hog(frame)
        else:
            return self._detect_silhouette(frame)

    def _detect_hog(self, frame: np.ndarray) -> Dict[str, Any]:
        orig_h, orig_w = frame.shape[:2]
        target_w = 400
        scale = target_w / float(orig_w)
        target_h = int(orig_h * scale)
        resized = cv2.resize(frame, (target_w, target_h))

        rects, weights = self.hog.detectMultiScale(
            resized,
            winStride=self.win_stride,
            padding=(4, 4),
            scale=1.05,
            hitThreshold=self.hit_threshold
        )

        detections = []
        top_conf = 0.0

        if len(rects) > 0:
            for i, (rx, ry, rw, rh) in enumerate(rects):
                weight = float(weights[i]) if len(weights) > i else 0.5
                norm_conf = min(1.0, max(0.1, (weight + 1.0) / 2.0))

                orig_x = int(rx / scale)
                orig_y = int(ry / scale)
                orig_w_box = int(rw / scale)
                orig_h_box = int(rh / scale)

                detections.append({
                    "bbox": [orig_x, orig_y, orig_w_box, orig_h_box],
                    "confidence": round(norm_conf, 3),
                    "label": "Person"
                })
                if norm_conf > top_conf:
                    top_conf = norm_conf

        return {
            "detections": detections,
            "person_count": len(detections),
            "top_confidence": round(top_conf, 3)
        }

    def _detect_silhouette(self, frame: np.ndarray) -> Dict[str, Any]:
        """Fallback vertical silhouette and contour aspect ratio detector for OpenCV builds without legacy objdetect."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        edges = cv2.Canny(blurred, 50, 150)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections = []
        top_conf = 0.0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 300:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = float(h) / float(w)
                # Human standing silhouette typically has aspect ratio between 1.6 and 3.5
                if 1.4 <= aspect_ratio <= 3.8 and h > 40:
                    conf = min(0.95, 0.4 + (area / (frame.shape[0] * frame.shape[1])) * 2.0)
                    detections.append({
                        "bbox": [x, y, w, h],
                        "confidence": round(conf, 3),
                        "label": "Person"
                    })
                    if conf > top_conf:
                        top_conf = conf

        return {
            "detections": detections,
            "person_count": len(detections),
            "top_confidence": round(top_conf, 3)
        }

