"""Ground-station pipeline coordinator running vision preprocessing and AI inference."""

import os
import time
from typing import Dict, Any, Optional
import cv2
import numpy as np

from vision.detection.camouflage_detector import CamouflageDetector
from vision.detection.person_detector import PersonDetector
from vision.visualization.overlay import render_hud_overlay, draw_detection_box
from vision.visualization.heatmap import generate_confidence_heatmap, blend_heatmap


class PipelineWorker:
    """Coordinates end-to-end processing of captured frames on the ground-station laptop."""

    def __init__(self, mode: str = "plan_a", save_results: bool = True, output_dir: str = "ground_station/results"):
        self.mode = mode.lower()
        self.save_results = save_results
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Initialize detector based on active operational mode
        if self.mode == "plan_b":
            self.detector = PersonDetector()
            print("[PIPELINE] Initialized Plan B Fallback Detector (Person Tracking)")
        else:
            self.detector = CamouflageDetector()
            print("[PIPELINE] Initialized Plan A Primary Detector (Camouflage Anomaly)")

        self.frame_count = 0
        self.fps = 0.0
        self.last_frame_time = time.time()

    def process_frame(self, frame: np.ndarray, drop_rate: float = 0.0, enable_heatmap: bool = False) -> tuple[np.ndarray, Dict[str, Any]]:
        """Process a single video frame and return annotated visualization and metrics."""
        start_t = time.time()
        self.frame_count += 1

        # Calculate instantaneous FPS
        dt = time.time() - self.last_frame_time
        if dt > 0:
            self.fps = 0.9 * self.fps + 0.1 * (1.0 / dt) if self.fps > 0 else (1.0 / dt)
        self.last_frame_time = time.time()

        # Execute detection model
        det_res = self.detector.detect(frame)
        latency_ms = (time.time() - start_t) * 1000.0

        # Build visual output
        annotated = frame.copy()

        # Draw detections
        detections = det_res.get("detections", [])
        for det in detections:
            bbox = det.get("bbox", [0, 0, 0, 0])
            score = det.get("confidence", 0.0)
            label = "CAMO_ANOMALY" if self.mode == "plan_a" else "PERSON"
            annotated = draw_detection_box(annotated, bbox, label=label, confidence=score)

        # Optional heatmap blending for Plan A
        if enable_heatmap and self.mode == "plan_a" and "probability_map" in det_res:
            heatmap = generate_confidence_heatmap(det_res["probability_map"])
            annotated = blend_heatmap(annotated, heatmap, alpha=0.35)

        # Render aerospace HUD header and telemetry
        telemetry = {
            "fps": round(self.fps, 1),
            "latency_ms": round(latency_ms, 1),
            "drop_rate": round(drop_rate, 1),
            "mode": self.mode.upper()
        }
        hud_frame = render_hud_overlay(annotated, telemetry)

        # Optionally save annotated result
        if self.save_results and self.frame_count % 30 == 0:
            save_path = os.path.join(self.output_dir, f"frame_{self.frame_count:06d}.jpg")
            cv2.imwrite(save_path, hud_frame)

        metrics = {
            "frame_id": self.frame_count,
            "latency_ms": latency_ms,
            "fps": self.fps,
            "detections": len(detections),
            "top_confidence": det_res.get("top_confidence", 0.0)
        }
        return hud_frame, metrics
