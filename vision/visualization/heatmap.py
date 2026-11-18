"""Anomaly confidence heatmap generation and alpha blending."""

import cv2
import numpy as np


def generate_confidence_heatmap(probability_map: np.ndarray, colormap: int = cv2.COLORMAP_TURBO) -> np.ndarray:
    """Transform a [0.0 - 1.0] probability map into a vibrant pseudo-color heatmap."""
    clipped = np.clip(probability_map * 255.0, 0, 255).astype(np.uint8)
    heatmap = cv2.applyColorMap(clipped, colormap)
    return heatmap


def blend_heatmap(frame: np.ndarray, heatmap: np.ndarray, alpha: float = 0.45) -> np.ndarray:
    """Alpha-blend color heatmap onto source terrain image."""
    if frame.shape[:2] != heatmap.shape[:2]:
        heatmap = cv2.resize(heatmap, (frame.shape[1], frame.shape[0]))
    blended = cv2.addWeighted(frame, 1.0 - alpha, heatmap, alpha, 0)
    return blended
