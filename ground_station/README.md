# SkyForge Ground Station Application

The Ground Station executes on a ground-station laptop or lab workstation. It ingests the live Wi-Fi stream from the drone's ESP32, applies OpenCV preprocessing, runs the active AIML model, displays real-time aerospace HUD telemetry, and logs evaluation results.

---

## 1. Directory Structure

```
ground_station/
├── receiver/
│   └── ground_receiver.py       # UDP socket server receiving JPEG stream
├── processing/
│   └── pipeline_worker.py       # Preprocessing, model inference & HUD compositor
├── results/                     # Timestamped annotated frames (.jpg)
├── logs/                        # Session telemetry CSV & diagnostic logs
└── README.md
```

---

## 2. Launching Ground Station

```bash
# Run Plan A (Primary Camouflage Detection) using synthetic feed for bench testing
python scripts/run_ground_station.py --mode plan_a --synthetic --enable-heatmap

# Run Plan B (Fallback Person Tracking) using live Wi-Fi stream from drone
python scripts/run_ground_station.py --mode plan_b --port 8080
```
