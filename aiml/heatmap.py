"""
==============================================================================
Team SkyForge-87: AI-Assisted ESP32 Tiny Drone with Camouflage Image Processing
Module: heatmap.py
Description: Visual Explainability Module.
             Extracts U-Net probability activation maps and renders
             COLORMAP_JET heatmaps overlaid onto the drone video feed.
==============================================================================
"""

from typing import Tuple
import cv2
import torch
import numpy as np

# Import teammate's predict module without modifying predict.py
import predict as pred_mod


def get_prob(frame: np.ndarray) -> np.ndarray:
    """
    Compute raw probability map at the input frame's native resolution.
    Reuses predict.py's normalization, device configuration, and U-Net model.

    :param frame: Input BGR image (H, W, 3).
    :return: Float32 probability map with shape (H, W) in range [0.0, 1.0].
    """
    h, w = frame.shape[:2]
    
    # 1. Resize to model's fixed input size (256x256)
    rgb = cv2.cvtColor(cv2.resize(frame, (pred_mod.SIZE, pred_mod.SIZE)), cv2.COLOR_BGR2RGB)
    
    # 2. ImageNet normalization
    x = (rgb.astype(np.float32) / 255.0 - pred_mod.MEAN) / pred_mod.STD
    x = torch.from_numpy(x.transpose(2, 0, 1))[None].to(pred_mod.device)
    
    # 3. Model forward pass + Sigmoid activation
    with torch.no_grad():
        prob = torch.sigmoid(pred_mod._model(x))[0, 0].cpu().numpy()
        
    # 4. Resize probability map back to original frame dimensions
    prob_map = cv2.resize(prob, (w, h))
    return prob_map.astype(np.float32)


def overlay_heatmap(frame: np.ndarray, prob_map: np.ndarray, alpha: float = 0.5) -> np.ndarray:
    """
    Create a pseudo-color activation heatmap overlay using cv2.COLORMAP_JET.

    :param frame: Original input BGR frame (H, W, 3).
    :param prob_map: Float probability map in range [0.0, 1.0].
    :param alpha: Blending weight for heatmap (1 - alpha weight for frame).
    :return: Blended BGR image showing camouflage detection intensity.
    """
    h, w = frame.shape[:2]
    
    # Ensure dimensions match
    if prob_map.shape[:2] != (h, w):
        prob_map = cv2.resize(prob_map, (w, h))
        
    # Scale float [0, 1] to uint8 [0, 255]
    clipped = np.clip(prob_map, 0.0, 1.0)
    heatmap_gray = np.uint8(255 * clipped)
    
    # Apply JET colormap: blue (low probability) -> green -> red (high camouflage activation)
    heatmap_color = cv2.applyColorMap(heatmap_gray, cv2.COLORMAP_JET)
    
    # Alpha blend with original video frame
    blended = cv2.addWeighted(heatmap_color, alpha, frame, 1.0 - alpha, 0)
    return blended


def predict_with_prob(frame: np.ndarray) -> Tuple[np.ndarray, float, np.ndarray]:
    """
    Single-pass prediction: runs the U-Net model ONCE and returns:
      1. annotated_frame (with red semi-transparent mask and green contour)
      2. confidence (mean probability over the mask, or 0.0 if empty)
      3. prob_map (float32 probability map of shape (H, W))

    Reuses predict.py's parameters (SIZE, MEAN, STD, device, _model) and threshold (0.30).
    Eliminates redundant inference overhead when both annotation and heatmap are needed.
    """
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(cv2.resize(frame, (pred_mod.SIZE, pred_mod.SIZE)), cv2.COLOR_BGR2RGB)
    x = (rgb.astype(np.float32) / 255.0 - pred_mod.MEAN) / pred_mod.STD
    x = torch.from_numpy(x.transpose(2, 0, 1))[None].to(pred_mod.device)
    
    with torch.no_grad():
        prob = torch.sigmoid(pred_mod._model(x))[0, 0].cpu().numpy()
        
    prob_map = cv2.resize(prob, (w, h)).astype(np.float32)
    mask = prob_map > 0.30
    conf = float(prob_map[mask].mean()) if mask.any() else 0.0

    out = frame.copy()
    out[mask] = (0.5 * out[mask] + 0.5 * np.array([0, 0, 255])).astype(np.uint8)
    cnts, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(out, cnts, -1, (0, 255, 0), 2)
    
    return out, conf, prob_map

