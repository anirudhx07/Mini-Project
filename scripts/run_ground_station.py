"""Launcher for the SkyForge ground-station receiver and AI detection pipeline."""

import os
import sys
import time
import argparse
import cv2

# Add workspace root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vision.capture.stream_receiver import StreamReceiver
from ground_station.processing.pipeline_worker import PipelineWorker


def main():
    parser = argparse.ArgumentParser(description="SkyForge Ground Station Runner")
    parser.add_argument("--mode", type=str, default="plan_a", choices=["plan_a", "plan_b"], help="Detection mode: plan_a (Camouflage) or plan_b (Person fallback)")
    parser.add_argument("--source", type=str, default="synthetic", help="Video source: 'synthetic', camera index (0, 1), or network URL")
    parser.add_argument("--synthetic", action="store_true", help="Force synthetic simulated terrain camera feed for bench testing")
    parser.add_argument("--enable-heatmap", action="store_true", help="Enable anomaly confidence heatmap overlay")
    parser.add_argument("--headless", action="store_true", help="Run without graphical GUI display (saves frames to disk)")
    parser.add_argument("--duration", type=int, default=0, help="Run duration in seconds (0 = continuous until keypress)")
    args = parser.parse_args()

    source = "synthetic" if args.synthetic else args.source
    print("=========================================================")
    print("   SKYFORGE GROUND STATION RUNNER v1.0")
    print(f"   Mode: {args.mode.upper()} | Source: {source}")
    print("=========================================================")

    receiver = StreamReceiver(source=source, target_fps=12.0)
    receiver.start()
    print("[OK] Video stream receiver thread started.")

    worker = PipelineWorker(mode=args.mode, save_results=True)
    start_time = time.time()

    try:
        while True:
            frame, ts = receiver.read(timeout=1.0)
            if frame is None:
                continue

            drop_rate = receiver.buffer.drop_rate()
            hud_frame, metrics = worker.process_frame(frame, drop_rate=drop_rate, enable_heatmap=args.enable_heatmap)

            if worker.frame_count % 15 == 0:
                print(f"[RUN] Frame {metrics['frame_id']:04d} | Latency: {metrics['latency_ms']:.1f}ms | FPS: {metrics['fps']:.1f} | Top Conf: {metrics['top_confidence']:.2f}")

            if not args.headless:
                cv2.imshow("SkyForge Telemetry Ground Station", hud_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == 27 or key == ord('q'): # ESC or q to exit
                    print("[INFO] Operator exit signal received.")
                    break

            if args.duration > 0 and (time.time() - start_time) >= args.duration:
                print(f"[INFO] Completed requested duration of {args.duration}s.")
                break

    except KeyboardInterrupt:
        print("\n[INFO] KeyboardInterrupt received. Shutting down cleanly...")
    finally:
        receiver.stop()
        if not args.headless:
            cv2.destroyAllWindows()
        print("[OK] Ground station shutdown complete.")


if __name__ == "__main__":
    main()
