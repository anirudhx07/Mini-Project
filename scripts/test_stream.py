"""Stream diagnostics and bench-testing tool to measure frame arrival rates and network drop."""

import os
import sys
import time
import argparse
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vision.capture.stream_receiver import StreamReceiver


def test_streaming(source: str, duration: int = 10):
    print(f"[BENCH] Initializing stream test from '{source}' for {duration} seconds...")
    receiver = StreamReceiver(source=source, target_fps=15.0)
    receiver.start()

    frame_intervals = []
    received_count = 0
    start_t = time.time()
    last_t = start_t

    try:
        while time.time() - start_t < duration:
            frame, ts = receiver.read(timeout=0.5)
            if frame is not None:
                now = time.time()
                dt = (now - last_t) * 1000.0
                last_t = now
                frame_intervals.append(dt)
                received_count += 1
            time.sleep(0.01)
    finally:
        receiver.stop()

    total_time = time.time() - start_t
    effective_fps = received_count / total_time if total_time > 0 else 0.0
    drop_pct = receiver.buffer.drop_rate()

    print("\n============== STREAM BENCHMARK REPORT ==============")
    print(f"Test Duration:         {total_time:.2f} s")
    print(f"Total Frames Ingested: {received_count}")
    print(f"Effective Frame Rate:  {effective_fps:.2f} FPS (Target: >= 5.0 FPS)")
    print(f"Buffer Drop Rate:      {drop_pct:.2f}% (Target: < 10.0%)")
    if frame_intervals:
        print(f"Mean Frame Interval:   {np.mean(frame_intervals):.1f} ms")
        print(f"Jitter StdDev:         {np.std(frame_intervals):.1f} ms")
    print("=====================================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=str, default="synthetic")
    parser.add_argument("--duration", type=int, default=10)
    args = parser.parse_args()

    test_streaming(args.source, args.duration)
