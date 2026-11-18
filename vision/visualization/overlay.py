"""Aerospace HUD graphics, targeting reticles, and diagnostic overlays."""

import cv2
import numpy as np
from typing import List, Dict, Any


def draw_detection_box(frame: np.ndarray, bbox: List[int], label: str = "TARGET", confidence: float = 0.0, color: tuple = (212, 245, 0)) -> np.ndarray:
    """Draw corner-bracketed aerospace targeting reticle around a target."""
    x, y, w, h = bbox
    img = frame.copy()
    line_len = max(8, int(min(w, h) * 0.25))
    thickness = 2

    # Draw 4 corner brackets instead of plain rectangle for aerospace look
    # Top-Left
    cv2.line(img, (x, y), (x + line_len, y), color, thickness)
    cv2.line(img, (x, y), (x, y + line_len), color, thickness)
    # Top-Right
    cv2.line(img, (x + w, y), (x + w - line_len, y), color, thickness)
    cv2.line(img, (x + w, y), (x + w, y + line_len), color, thickness)
    # Bottom-Left
    cv2.line(img, (x, y + h), (x + line_len, y + h), color, thickness)
    cv2.line(img, (x, y + h), (x, y + h - line_len), color, thickness)
    # Bottom-Right
    cv2.line(img, (x + w, y + h), (x + w - line_len, y + h), color, thickness)
    cv2.line(img, (x + w, y + h), (x + w, y + h - line_len), color, thickness)

    # Text badge
    tag = f"{label} [{int(confidence * 100)}%]"
    cv2.putText(img, tag, (x, max(15, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
    return img


def render_hud_overlay(frame: np.ndarray, telemetry: Dict[str, Any]) -> np.ndarray:
    """Renders comprehensive telemetry HUD on ground station feed."""
    hud = frame.copy()
    h, w = hud.shape[:2]

    # Cyan HUD Color: (212, 245, 0) in BGR = #00F5D4
    hud_color = (212, 245, 0)
    text_color = (255, 251, 248) # Cloud white

    # Header Telemetry Bar
    cv2.rectangle(hud, (0, 0), (w, 24), (64, 26, 6), -1) # Midnight navy background
    cv2.line(hud, (0, 24), (w, 24), hud_color, 1)

    fps = telemetry.get("fps", 0.0)
    latency = telemetry.get("latency_ms", 0.0)
    drop_rate = telemetry.get("drop_rate", 0.0)
    mode = telemetry.get("mode", "PLAN_A")

    header_text = f"SKYFORGE // MODE: {mode} | FPS: {fps:4.1f} | LATENCY: {latency:4.0f}ms | DROP: {drop_rate:3.1f}%"
    cv2.putText(hud, header_text, (10, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.42, text_color, 1, cv2.LINE_AA)

    # Central Boresight Crosshair
    cx, cy = w // 2, h // 2
    cv2.line(hud, (cx - 15, cy), (cx - 5, cy), hud_color, 1)
    cv2.line(hud, (cx + 5, cy), (cx + 15, cy), hud_color, 1)
    cv2.line(hud, (cx, cy - 15), (cx, cy - 5), hud_color, 1)
    cv2.line(hud, (cx, cy + 5), (cx, cy + 15), hud_color, 1)
    cv2.circle(hud, (cx, cy), 2, hud_color, -1)

    # Footer Status
    footer_text = "GLA UNIVERSITY // AIML LAB TEAM 87"
    cv2.putText(hud, footer_text, (10, h - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (240, 201, 76), 1, cv2.LINE_AA)

    return hud
