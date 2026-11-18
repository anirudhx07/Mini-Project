"""Gradient computation and texture feature extraction."""

import cv2
import numpy as np


def compute_gradient_magnitude(image: np.ndarray, ksize: int = 3) -> np.ndarray:
    """Calculate gradient magnitude using Sobel operators."""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=ksize)
    grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=ksize)

    magnitude = cv2.magnitude(grad_x, grad_y)
    norm_mag = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX)
    return norm_mag.astype(np.uint8)


def extract_texture_edges(image: np.ndarray, low_thresh: int = 50, high_thresh: int = 150) -> np.ndarray:
    """Extract multi-scale structural boundaries with Canny edge detector."""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    blurred = cv2.GaussianBlur(gray, (5, 5), 1.2)
    edges = cv2.Canny(blurred, low_thresh, high_thresh)
    return edges
