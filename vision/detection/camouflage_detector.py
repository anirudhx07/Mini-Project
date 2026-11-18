"""Plan A: Camouflage anomaly detector combining texture gradients and local contrast analysis."""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Any
from ..preprocessing.filters import apply_bilateral_filter, morphological_cleanup
from ..preprocessing.contrast_enhancement import apply_clahe
from ..preprocessing.edge_detection import compute_gradient_magnitude


class CamouflageDetector:
    """Detects visual camouflage and anomalous texture regions against natural terrain backgrounds."""

    def __init__(self, sensitivity: float = 0.65, min_contour_area: int = 150):
        self.sensitivity = sensitivity
        self.min_contour_area = min_contour_area

    def detect(self, frame: np.ndarray) -> Dict[str, Any]:
        """Process a terrain frame and return anomalous camouflage candidate regions.
        
        Returns:
            Dict containing:
                - 'mask': binary detection mask (uint8, 0 or 255)
                - 'probability_map': float32 normalized confidence heatmap [0.0 - 1.0]
                - 'detections': List of bounding boxes [x, y, w, h, score]
                - 'top_confidence': float [0.0 - 1.0]
        """
        # Step 1: Preprocess with CLAHE and bilateral smoothing
        enhanced = apply_clahe(frame, clip_limit=2.5)
        filtered = apply_bilateral_filter(enhanced, d=5, sigma_color=40, sigma_space=40)

        # Step 2: Multi-feature texture and edge discrepancy map
        gray = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)
        grad_mag = compute_gradient_magnitude(gray)

        # Compute local standard deviation (texture energy)
        mean_img = cv2.blur(gray.astype(np.float32), (9, 9))
        sq_mean = cv2.blur((gray.astype(np.float32))**2, (9, 9))
        variance = np.maximum(0.0, sq_mean - mean_img**2)
        texture_energy = np.sqrt(variance)

        # Normalize texture energy to [0, 255]
        texture_norm = cv2.normalize(texture_energy, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        # Fuse gradient magnitude and texture anomaly
        anomaly_score = cv2.addWeighted(grad_mag, 0.5, texture_norm, 0.5, 0)
        prob_map = (anomaly_score.astype(np.float32) / 255.0)

        # Step 3: Adaptive thresholding based on sensitivity
        thresh_val = int(255 * (1.0 - (self.sensitivity * 0.4)))
        _, binary_mask = cv2.threshold(anomaly_score, thresh_val, 255, cv2.THRESH_BINARY)
        cleaned_mask = morphological_cleanup(binary_mask, kernel_size=5)

        # Step 4: Extract candidate contours and score regions
        contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections = []
        top_conf = 0.0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area >= self.min_contour_area:
                x, y, w, h = cv2.boundingRect(cnt)
                # Compute average confidence inside this region
                roi = prob_map[y:y+h, x:x+w]
                score = float(np.mean(roi)) if roi.size > 0 else 0.0

                detections.append({
                    "bbox": [x, y, w, h],
                    "area": float(area),
                    "confidence": round(score, 3)
                })
                if score > top_conf:
                    top_conf = score

        return {
            "mask": cleaned_mask,
            "probability_map": prob_map,
            "detections": detections,
            "top_confidence": round(top_conf, 3)
        }
