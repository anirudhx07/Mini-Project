import numpy as np
import pytest
import cv2

from vision.preprocessing.filters import apply_bilateral_filter, denoise_frame, morphological_cleanup
from vision.preprocessing.contrast_enhancement import apply_clahe, normalize_illumination
from vision.preprocessing.edge_detection import compute_gradient_magnitude, extract_texture_edges


def test_filters():
    img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    filtered = apply_bilateral_filter(img, d=5, sigma_color=30, sigma_space=30)
    assert filtered.shape == img.shape
    assert filtered.dtype == np.uint8

    denoised = denoise_frame(img, ksize=3)
    assert denoised.shape == img.shape


def test_clahe_contrast():
    img = np.full((120, 160, 3), 100, dtype=np.uint8)
    # Add localized contrast
    img[40:80, 50:90] = 180
    enhanced = apply_clahe(img, clip_limit=2.0)
    assert enhanced.shape == img.shape
    assert enhanced.dtype == np.uint8


def test_edge_detection():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.circle(img, (50, 50), 20, (255, 255, 255), -1)
    
    grad = compute_gradient_magnitude(img)
    assert grad.shape == (100, 100)
    assert np.max(grad) > 0

    edges = extract_texture_edges(img)
    assert edges.shape == (100, 100)
