"""
==============================================================================
Team SkyForge-87: AI-Assisted ESP32 Tiny Drone with Camouflage Image Processing
Module: preprocess.py
Description: Preprocessing module for standardizing resolution and optional
             CLAHE contrast enhancement on the L-channel of LAB color space.
==============================================================================
"""

from typing import Tuple, Optional
import cv2
import numpy as np

# Standardized resolution for drone vision pipeline (width, height)
TARGET_SIZE = (320, 240)

# Default CLAHE hyperparameters
DEFAULT_CLIP_LIMIT = 2.0
DEFAULT_TILE_GRID_SIZE = (8, 8)


def apply_clahe(frame: np.ndarray,
                clip_limit: float = DEFAULT_CLIP_LIMIT,
                tile_grid_size: Tuple[int, int] = DEFAULT_TILE_GRID_SIZE) -> np.ndarray:
    """
    Apply Contrast Limited Adaptive Histogram Equalization (CLAHE) on the L channel of LAB space.

    Why LAB?
    - L = Lightness, A/B = Color/Chrominance channels.
    - Enhancing only L boosts contrast and visibility in shadows/glare without chromatic distortion.

    :param frame: Input BGR image (H, W, 3), dtype uint8.
    :param clip_limit: CLAHE threshold for contrast limiting (default 2.0).
    :param tile_grid_size: Neighborhood tile size for local equalization (default (8, 8)).
    :return: Contrast-enhanced BGR image (H, W, 3), dtype uint8.
    """
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    l_eq = clahe.apply(l)
    return cv2.cvtColor(cv2.merge((l_eq, a, b)), cv2.COLOR_LAB2BGR)


def preprocess(frame: np.ndarray,
               target_size: Optional[Tuple[int, int]] = TARGET_SIZE,
               use_clahe: bool = False,
               clip_limit: float = DEFAULT_CLIP_LIMIT,
               tile_grid_size: Tuple[int, int] = DEFAULT_TILE_GRID_SIZE) -> Optional[np.ndarray]:
    """
    Standardize frame resolution and optionally apply CLAHE contrast enhancement.

    :param frame: Raw input BGR image (H, W, 3), dtype uint8.
    :param target_size: Output (width, height) tuple, e.g. (320, 240).
    :param use_clahe: If True, apply CLAHE on L channel; if False, return frame unchanged.
    :param clip_limit: CLAHE clipLimit (default 2.0).
    :param tile_grid_size: CLAHE tileGridSize (default (8, 8)).
    :return: Processed BGR image with shape (height, width, 3), dtype uint8.
    """
    if frame is None:
        return None

    # Step 1: Standardize resolution if target_size is specified
    if target_size is not None:
        target_w, target_h = target_size
        if frame.shape[1] != target_w or frame.shape[0] != target_h:
            frame = cv2.resize(frame, (target_w, target_h))

    # Step 2: Apply CLAHE if enabled; otherwise return frame unchanged
    if use_clahe:
        return apply_clahe(frame, clip_limit=clip_limit, tile_grid_size=tile_grid_size)

    return frame


def enhance(frame: np.ndarray,
            target_size: Optional[Tuple[int, int]] = TARGET_SIZE,
            clip_limit: float = DEFAULT_CLIP_LIMIT,
            tile_grid_size: Tuple[int, int] = DEFAULT_TILE_GRID_SIZE) -> Optional[np.ndarray]:
    """
    Backward-compatible helper function that applies resize + CLAHE (use_clahe=True).
    Reused by existing evaluation and evidence generation scripts.
    """
    return preprocess(frame, target_size=target_size, use_clahe=True,
                      clip_limit=clip_limit, tile_grid_size=tile_grid_size)
