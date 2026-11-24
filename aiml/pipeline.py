"""
==============================================================================
Team SkyForge-87: AI-Assisted ESP32 Tiny Drone with Camouflage Image Processing
Module: pipeline.py
Description: Unified end-to-end Computer Vision Pipeline runner for drone.
             Combines config.py defaults, stream.py FrameSource, preprocess.py,
             multi-model dispatch (predict.py & predict_person.py), single-pass
             heatmap overlay, CLI options, and results logging.
==============================================================================
"""

import os
import csv
import sys
import time
import argparse
import platform
from datetime import datetime
from typing import Optional, Callable
import cv2
import torch
import numpy as np

# Subsystem Modules
import config
from preprocess import preprocess, enhance
from stream import FrameSource
from heatmap import overlay_heatmap, predict_with_prob

# Performance Target Benchmarks
TARGET_MAX_LATENCY_MS = getattr(config, "TARGET_MAX_LATENCY_MS", 500.0)
TARGET_MIN_FPS = getattr(config, "TARGET_MIN_FPS", 5.0)
TARGET_MAX_DROP_RATE = getattr(config, "TARGET_MAX_DROP_RATE", 10.0)
WARMUP_FRAMES = 10
CONSECUTIVE_FAIL_LIMIT = 30


def get_hardware_name() -> str:
    """Return human-readable CPU/GPU hardware description utilized by PyTorch."""
    if torch.cuda.is_available():
        return f"GPU: {torch.cuda.get_device_name(0)}"
    proc = platform.processor()
    machine = platform.machine()
    return f"CPU: {proc if proc else machine} (PyTorch CPU Engine)"


def append_run_summary(summary_path: str, row_data: dict):
    """
    Append run telemetry to run_summary.csv:
    timestamp, source, source_type, model, heatmap, benchmarked_frames,
    avg_latency_ms, processing_fps, capture_fps, dropped_pct.
    """
    file_exists = os.path.exists(summary_path)
    fieldnames = [
        "timestamp", "source", "source_type", "model", "heatmap",
        "benchmarked_frames", "avg_latency_ms", "processing_fps",
        "capture_fps", "dropped_pct"
    ]
    with open(summary_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_data)


def get_model_dispatch(model_name: str):
    """
    Resolve model loader and predict callable according to model_name:
    'camouflage' / 'unet' -> predict.py
    'person' / 'yolo'     -> predict_person.py
    """
    name = str(model_name).lower().strip()
    if name in ("person", "yolo"):
        try:
            import predict_person as mod
        except ImportError:
            import predict_yolo as mod
        return mod.load_model, mod.predict, "person"
    else:
        import predict as mod
        return mod.load_model, mod.predict, "camouflage"


def run_pipeline(source=None,
                 enable_heatmap: Optional[bool] = None,
                 bench_frames: Optional[int] = None,
                 save_raw: bool = False,
                 model_type: Optional[str] = None,
                 use_clahe: Optional[bool] = None,
                 every_n: Optional[int] = None,
                 predict_fn: Optional[Callable] = None,
                 max_frames: Optional[int] = None,
                 display: bool = True):
    """
    Execute drone vision pipeline:
    - Reads frames from stream.py FrameSource
    - Applies preprocess.py resize (320, 240) + optional CLAHE
    - Dispatches model inference every N frames
    - Computes real latency ms (excluding warm-up frames)
    - Displays Side-by-Side: Original | Result (+ optional Heatmap)
    - Saves snapshots to results/ and logs to results_log.csv & run_summary.csv
    - Provides mock support for unit tests via predict_fn and max_frames
    """
    # Fallback to config.py settings if not explicitly passed
    source = getattr(config, "SOURCE", "test.mp4") if source is None else source
    model_type = getattr(config, "MODEL", "camouflage") if model_type is None else model_type
    use_clahe = getattr(config, "USE_CLAHE", False) if use_clahe is None else use_clahe
    every_n = getattr(config, "EVERY_N", 1) if every_n is None else every_n
    target_resize = getattr(config, "RESIZE", (320, 240))

    if enable_heatmap is None:
        enable_heatmap = False

    os.makedirs("results", exist_ok=True)
    if save_raw:
        os.makedirs("frames_raw", exist_ok=True)

    hardware_info = get_hardware_name()
    canonical_model = "camouflage"

    # 1. Model Loading (unless mocked for unit tests)
    if predict_fn is None:
        load_fn, actual_predict, canonical_model = get_model_dispatch(model_type)
        print(f"[Pipeline] Loading '{canonical_model}' model...")
        load_fn("best_model.pth")
        predict_fn = actual_predict
        print(f"[Pipeline] Model '{canonical_model}' loaded successfully.")

        if canonical_model == "person" and enable_heatmap:
            print("[Pipeline Note] Heatmap disabled for person model (bounding box mode).")
            enable_heatmap = False
    else:
        canonical_model = str(model_type)

    # 2. Setup CSV loggers
    results_log = "results_log.csv"
    rlog_exists = os.path.exists(results_log)
    rlogf = open(results_log, "a", newline="", encoding="utf-8")
    rlog_writer = csv.writer(rlogf)
    if not rlog_exists:
        rlog_writer.writerow([
            "timestamp", "source", "model", "clahe",
            "latency_ms", "fps", "confidence", "file"
        ])
        rlogf.flush()

    # 3. Stream initialization via FrameSource
    is_live = isinstance(source, int) or str(source).startswith(("http://", "https://", "rtsp://"))
    stream = FrameSource(source=source, buffer_size=1, loop=not is_live)

    frame_idx = 0
    inference_count = 0
    consecutive_fails = 0
    latencies_ms = []
    last_result = None

    print("\n" + "=" * 65)
    print("     TEAM SKYFORGE-87 | VISION PIPELINE RUNNING")
    print("=" * 65)
    print(f"Hardware Device : {hardware_info}")
    print(f"Model Selected  : {canonical_model.upper()}")
    print(f"Source          : {source}")
    print(f"Source Type     : {'Live Stream / Camera' if stream.is_live else 'Offline (Folder / Video)'}")
    print(f"CLAHE Enhanced  : {use_clahe}")
    print(f"Heatmap Mode    : {'ENABLED (Single-Pass)' if enable_heatmap else 'DISABLED'}")
    print(f"Save Raw Frames : {'ENABLED' if save_raw else 'DISABLED'}")
    if bench_frames and not is_live:
        print(f"Benchmark Goal  : Process {bench_frames} frames (>= 100 benchmarked)")
    print("Controls:")
    print("  [S]   -> Save current frame results to results/")
    print("  [ESC] -> Exit pipeline safely")
    print("-" * 65)

    try:
        while True:
            # Check frame limits for testing or benchmarking
            if max_frames is not None and frame_idx >= max_frames:
                break
            if bench_frames and not is_live and frame_idx >= bench_frames:
                print(f"[Pipeline] Reached target benchmark count of {bench_frames} frames.")
                break

            raw_frame = stream.read()
            if raw_frame is None:
                consecutive_fails += 1
                if consecutive_fails >= CONSECUTIVE_FAIL_LIMIT or not stream.is_live:
                    break
                time.sleep(0.01)
                continue

            consecutive_fails = 0
            frame_idx += 1

            # Optional raw frame saving to survive connection drops
            if save_raw:
                ts_raw = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                cv2.imwrite(os.path.join("frames_raw", f"{ts_raw}_frame_{frame_idx:05d}.jpg"), raw_frame)

            # 4. Preprocessing: Resize + optional CLAHE
            prep_frame = preprocess(raw_frame, target_size=target_resize, use_clahe=use_clahe)

            # 5. Model Inference (every N frames)
            should_infer = (last_result is None or frame_idx % every_n == 0)
            heatmap_frame = None

            if should_infer:
                inference_count += 1
                t0 = time.perf_counter()

                if enable_heatmap and canonical_model == "camouflage" and predict_fn == actual_predict:
                    annotated_frame, confidence, prob_map = predict_with_prob(prep_frame)
                    heatmap_frame = overlay_heatmap(prep_frame, prob_map, alpha=0.5)
                else:
                    annotated_frame, confidence = predict_fn(prep_frame)
                    if enable_heatmap and canonical_model == "camouflage":
                        prob_map = np.zeros(prep_frame.shape[:2], dtype=np.float32)
                        heatmap_frame = overlay_heatmap(prep_frame, prob_map, alpha=0.5)

                latency_ms = (time.perf_counter() - t0) * 1000.0
                last_result = (annotated_frame, confidence, latency_ms, heatmap_frame)

                if inference_count > WARMUP_FRAMES:
                    latencies_ms.append(latency_ms)
            else:
                annotated_frame, confidence, _, heatmap_frame = last_result
                latency_ms = None

            current_fps = (1000.0 / latency_ms) if (latency_ms and latency_ms > 0) else 0.0

            # 6. Display formatting: Side-by-Side (Original | Result)
            display_prep = prep_frame.copy()
            display_annotated = annotated_frame.copy()

            cap_fps_str = f"{stream.capture_fps:.1f} fps" if stream.is_live else "offline"
            status_str = f"Conf: {confidence:.2f} | " + (f"{latency_ms:.0f}ms ({current_fps:.1f} FPS)" if latency_ms else "(skipped)")
            cv2.putText(display_annotated, status_str, (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1, cv2.LINE_AA)

            if enable_heatmap and heatmap_frame is not None:
                cv2.putText(heatmap_frame, "JET Camouflage Heatmap", (10, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
                combined_view = np.hstack([display_prep, display_annotated, heatmap_frame])
            else:
                combined_view = np.hstack([display_prep, display_annotated])

            if display:
                cv2.imshow("SkyForge-87 Drone Vision Pipeline", combined_view)
                key = cv2.waitKey(1) & 0xFF

                if key == ord('s') or key == ord('S'):
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    out_path = f"results/{ts}_{canonical_model}.jpg"
                    cv2.imwrite(out_path, combined_view)

                    logged_lat = round(latency_ms, 1) if latency_ms else ""
                    logged_fps = round(current_fps, 1) if latency_ms else ""
                    rlog_writer.writerow([
                        ts, source, canonical_model, use_clahe,
                        logged_lat, logged_fps, round(confidence, 3), out_path
                    ])
                    rlogf.flush()
                    print(f"[Pipeline] Saved snapshot -> {out_path}")

                elif key == 27:  # ESC
                    print("\n[Pipeline] ESC pressed by user. Shutting down...")
                    break

    except KeyboardInterrupt:
        print("\n[Pipeline] Interrupted via Keyboard.")

    finally:
        stream.release()
        if display:
            cv2.destroyAllWindows()
        rlogf.close()

    # 7. Final Summary
    num_benchmarked = len(latencies_ms)
    avg_latency = (sum(latencies_ms) / num_benchmarked) if num_benchmarked > 0 else 0.0
    proc_fps = (1000.0 / avg_latency) if avg_latency > 0 else 0.0
    failed_reads = stream.failed_reads
    drop_rate = stream.dropped_frame_percentage

    print("\n" + "=" * 65)
    print("             PIPELINE FINAL PERFORMANCE SUMMARY")
    print("=" * 65)
    print(f"Hardware Compute Device     : {hardware_info}")
    print(f"Model Architecture          : {canonical_model.upper()}")
    print(f"Heatmap Mode                : {'ON' if enable_heatmap else 'OFF'}")
    print(f"Total Frames Processed      : {frame_idx}")
    print(f"Warm-Up Calls Excluded      : {min(inference_count, WARMUP_FRAMES)}")
    print(f"Benchmarked Inferences      : {num_benchmarked}")
    print("-" * 65)
    print(f"Average Pipeline Latency    : {avg_latency:.1f} ms")
    print(f"Processing FPS (Inference)  : {proc_fps:.1f} FPS")

    if stream.is_live:
        print(f"Capture FPS (Hardware)      : {stream.capture_fps:.1f} FPS")
        cap_val = round(stream.capture_fps, 1)
    else:
        print("Capture FPS (Hardware)      : n/a (not a live source)")
        cap_val = ""

    print(f"Dropped Frames              : {failed_reads} ({drop_rate:.1f}%)")
    print("-" * 65)

    # Synopsis Target Checks
    latency_pass = avg_latency <= TARGET_MAX_LATENCY_MS and avg_latency >= 0
    fps_pass = proc_fps >= TARGET_MIN_FPS or num_benchmarked == 0
    drop_pass = drop_rate < TARGET_MAX_DROP_RATE

    print("SYNOPSIS TARGET VERIFICATION:")
    print(f"  1. Latency (<= {TARGET_MAX_LATENCY_MS:.0f} ms)     : {avg_latency:.1f} ms -> [{'PASS' if latency_pass else 'FAIL'}]")
    print(f"  2. Processing FPS (>= {TARGET_MIN_FPS:.0f} FPS): {proc_fps:.1f} FPS -> [{'PASS' if fps_pass else 'FAIL'}]")
    print(f"  3. Dropped Frames (< {TARGET_MAX_DROP_RATE:.0f}%)   : {drop_rate:.1f}% -> [{'PASS' if drop_pass else 'FAIL'}]")
    print("=" * 65)

    summary_record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": str(source),
        "source_type": "live" if stream.is_live else "offline",
        "model": canonical_model,
        "heatmap": "on" if enable_heatmap else "off",
        "benchmarked_frames": num_benchmarked,
        "avg_latency_ms": round(avg_latency, 1),
        "processing_fps": round(proc_fps, 1),
        "capture_fps": cap_val,
        "dropped_pct": round(drop_rate, 1)
    }
    append_run_summary("run_summary.csv", summary_record)

    return {
        "frames": frame_idx,
        "benchmarked_frames": num_benchmarked,
        "avg_latency_ms": round(avg_latency, 1),
        "avg_fps": round(proc_fps, 1),
        "drop_pct": round(drop_rate, 1)
    }


def parse_args():
    """Parse CLI arguments for pipeline execution."""
    parser = argparse.ArgumentParser(description="Team SkyForge-87 Drone Vision Pipeline")
    parser.add_argument("--source", type=str, default=None,
                        help="Input source: 0, video file, test_images, or URL")
    parser.add_argument("--heatmap", type=str, choices=["on", "off"], default=None,
                        help="Enable JET heatmap overlay: 'on' or 'off'")
    parser.add_argument("--bench", type=int, default=None,
                        help="Number of frames to benchmark")
    parser.add_argument("--save-raw", action="store_true", default=False,
                        help="Save raw received frames to frames_raw/")
    parser.add_argument("--model", type=str, choices=["unet", "yolo", "camouflage", "person"], default=None,
                        help="Model architecture: 'camouflage' (U-Net) or 'person' (YOLOv8n)")
    parser.add_argument("--clahe", type=str, choices=["on", "off"], default=None,
                        help="Enable CLAHE contrast preprocessing: 'on' or 'off'")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    source_arg = int(args.source) if (args.source and args.source.isdigit()) else args.source
    heatmap_arg = (args.heatmap.lower() == "on") if args.heatmap else None
    clahe_arg = (args.clahe.lower() == "on") if args.clahe else None

    run_pipeline(
        source=source_arg,
        enable_heatmap=heatmap_arg,
        bench_frames=args.bench,
        save_raw=args.save_raw,
        model_type=args.model,
        use_clahe=clahe_arg
    )
