"""Adaptive contrast enhancement and illumination correction."""

import cv2
import numpy as np


def apply_clahe(image: np.ndarray, clip_limit: float = 2.5, tile_grid_size: tuple[int, int] = (8, 8)) -> np.ndarray:
    """Enhance localized contrast using Contrast Limited Adaptive Histogram Equalization.
    
    Operates on the L-channel in LAB space to preserve natural chromatic balances.
    """
    if len(image.shape) == 2:
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        return clahe.apply(image)
    
    # Convert BGR to LAB color space
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    l_enhanced = clahe.apply(l_channel)

    merged = cv2.merge([l_enhanced, a_channel, b_channel])
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)


def normalize_illumination(image: np.ndarray) -> np.ndarray:
    """Normalize global scene lighting using min-max linear scaling per channel."""
    norm_img = np.zeros_like(image, dtype=np.float32)
    for c in range(image.shape[2] if len(image.shape) == 3 else 1):
        ch = image[:, :, c] if len(image.shape) == 3 else image
        min_val, max_val = np.min(ch), np.max(ch)
        if max_val - min_val > 1e-5:
            norm_ch = (ch - min_val) / (max_val - min_val) * 255.0
        else:
            norm_ch = ch
        if len(image.shape) == 3:
            norm_img[:, :, c] = norm_ch
        else:
            norm_img = norm_ch
    return np.clip(norm_img, 0, 255).astype(np.uint8)
