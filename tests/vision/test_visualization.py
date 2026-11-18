import numpy as np
import pytest

from vision.visualization.overlay import draw_detection_box, render_hud_overlay
from vision.visualization.heatmap import generate_confidence_heatmap, blend_heatmap


def test_hud_overlay():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    telemetry = {"fps": 12.5, "latency_ms": 48.0, "drop_rate": 2.1, "mode": "PLAN_A"}
    hud = render_hud_overlay(frame, telemetry)
    assert hud.shape == frame.shape
    # Check that pixels were drawn
    assert np.any(hud > 0)


def test_detection_box():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    boxed = draw_detection_box(frame, [50, 50, 80, 60], label="CAMO", confidence=0.88)
    assert boxed.shape == frame.shape
    assert np.any(boxed > 0)


def test_heatmap():
    prob_map = np.linspace(0.0, 1.0, 100 * 100).reshape((100, 100)).astype(np.float32)
    heatmap = generate_confidence_heatmap(prob_map)
    assert heatmap.shape == (100, 100, 3)

    frame = np.full((100, 100, 3), 128, dtype=np.uint8)
    blended = blend_heatmap(frame, heatmap, alpha=0.5)
    assert blended.shape == (100, 100, 3)
