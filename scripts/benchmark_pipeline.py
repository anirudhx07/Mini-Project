"""Profiles stage-by-stage wall-clock latency across the computer vision pipeline."""

import os
import sys
import time
import numpy as np
import cv2

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vision.preprocessing.filters import apply_bilateral_filter
from vision.preprocessing.contrast_enhancement import apply_clahe
from vision.detection.camouflage_detector import CamouflageDetector
from vision.detection.person_detector import PersonDetector
from vision.visualization.overlay import render_hud_overlay, draw_detection_box


def benchmark_pipeline(num_iterations: int = 50):
    print(f"[BENCHMARK] Executing {num_iterations} pipeline iterations on 320x240 frame...")

    # Generate synthetic benchmark frame
    frame = np.random.randint(50, 180, (240, 320, 3), dtype=np.uint8)

    camo_detector = CamouflageDetector()
    person_detector = PersonDetector()

    times = {
        "clahe": [],
        "bilateral": [],
        "camo_detect": [],
        "person_detect": [],
        "hud_render": []
    }

    for _ in range(num_iterations):
        # 1. CLAHE
        t0 = time.perf_counter()
        enhanced = apply_clahe(frame)
        times["clahe"].append((time.perf_counter() - t0) * 1000.0)

        # 2. Bilateral Filter
        t0 = time.perf_counter()
        filtered = apply_bilateral_filter(enhanced)
        times["bilateral"].append((time.perf_counter() - t0) * 1000.0)

        # 3. Plan A Camouflage Detection
        t0 = time.perf_counter()
        camo_res = camo_detector.detect(frame)
        times["camo_detect"].append((time.perf_counter() - t0) * 1000.0)

        # 4. Plan B Person Detection (evaluated every 5th iter for speed)
        if _ % 5 == 0:
            t0 = time.perf_counter()
            person_res = person_detector.detect(frame)
            times["person_detect"].append((time.perf_counter() - t0) * 1000.0)

        # 5. HUD Rendering
        t0 = time.perf_counter()
        annotated = draw_detection_box(frame, [100, 80, 60, 40], label="BENCH", confidence=0.85)
        hud = render_hud_overlay(annotated, {"fps": 15.0, "latency_ms": 50.0, "drop_rate": 0.0, "mode": "BENCH"})
        times["hud_render"].append((time.perf_counter() - t0) * 1000.0)

    print("\n================ PIPELINE LATENCY PROFILE ================")
    print(f"CLAHE Contrast Enhancement:    {np.mean(times['clahe']):6.2f} ms  (std: {np.std(times['clahe']):.2f} ms)")
    print(f"Bilateral Spatial Denoising:   {np.mean(times['bilateral']):6.2f} ms  (std: {np.std(times['bilateral']):.2f} ms)")
    print(f"Plan A Camouflage Detection:   {np.mean(times['camo_detect']):6.2f} ms  (std: {np.std(times['camo_detect']):.2f} ms)")
    print(f"Plan B Person Detection (HOG): {np.mean(times['person_detect']):6.2f} ms  (std: {np.std(times['person_detect']):.2f} ms)")
    print(f"HUD Compositing & Overlays:    {np.mean(times['hud_render']):6.2f} ms  (std: {np.std(times['hud_render']):.2f} ms)")
    
    total_plan_a = np.mean(times["clahe"]) + np.mean(times["bilateral"]) + np.mean(times["camo_detect"]) + np.mean(times["hud_render"])
    print("----------------------------------------------------------")
    print(f"TOTAL PLAN A FRAME LATENCY:    {total_plan_a:6.2f} ms  (Target: <= 500 ms) -> {'PASS' if total_plan_a <= 500 else 'FAIL'}")
    print("==========================================================\n")


if __name__ == "__main__":
    benchmark_pipeline()
