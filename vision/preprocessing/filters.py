"""Noise reduction and spatial filtering utilities."""

import cv2
import numpy as np


def apply_bilateral_filter(image: np.ndarray, d: int = 7, sigma_color: float = 50.0, sigma_space: float = 50.0) -> np.ndarray:
    """Apply bilateral filtering to smooth textures while preserving salient boundaries."""
    return cv2.bilateralFilter(image, d=d, sigmaColor=sigma_color, sigmaSpace=sigma_space)


def denoise_frame(image: np.ndarray, ksize: int = 3) -> np.ndarray:
    """Apply median blurring to remove impulse/salt-and-pepper sensor noise."""
    if ksize % 2 == 0:
        ksize += 1
    return cv2.medianBlur(image, ksize)


def morphological_cleanup(mask: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """Apply opening and closing morphology to eliminate isolated noise pixels."""
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
    return closed
