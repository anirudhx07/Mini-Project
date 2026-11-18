# SkyForge Software & Development Setup Guide

This guide details the installation, configuration, and execution workflow for both the embedded ESP32 firmware and the ground-station computer vision environment.

---

## 1. System Requirements & Toolchain

### Hardware & Operating Systems
- **Ground Station:** Linux (Ubuntu 22.04+), macOS, or Windows 10/11 with Python 3.10+.
- **Embedded Target:** ESP32 / ESP32-S3 dual-core microcontroller module.
- **Hardware Programmer:** Micro-USB / USB-C data cable (confirm cable supports data, not power-only).

### Required Tooling
- [VS Code](https://code.visualstudio.com/) with the [PlatformIO IDE](https://platformio.org/) extension installed.
- Python 3.10 or higher.
- Git version control.

---

## 2. Ground Station Setup (Python Environment)

### Step 1: Clone Repository
```bash
git clone https://github.com/SkyForge/SkyForge.git
cd SkyForge
```

### Step 2: Establish Python Virtual Environment
```bash
# On Linux / macOS
python3 -m venv venv
source venv/bin/activate

# On Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Pinned Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Verify Environment Integrity
Run the automated test suite to ensure OpenCV, NumPy, and PyTorch dependencies are correctly installed:
```bash
pytest tests/ -v
```

---

## 3. Firmware Configuration & Flashing

The embedded firmware is organized under `firmware/` using PlatformIO.

```
firmware/
├── drone_controller/       # Onboard flight stabilization & Wi-Fi stream
│   ├── platformio.ini
│   ├── include/config.h
│   └── src/main.cpp
└── remote_controller/      # Ground remote transmitter
    ├── platformio.ini
    ├── include/config.h
    └── src/main.cpp
```

### Step 1: Configure Network Credentials
Navigate to `firmware/drone_controller/include/`:
```bash
cd firmware/drone_controller/include/
cp config.h.example config.h
```
Edit `config.h` with your local Wi-Fi router or access point credentials:
```cpp
// Wi-Fi Access Point / Station Configuration
#define WIFI_SSID     "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// Ground Station Target Host
#define GROUND_STATION_IP   "192.168.1.100"
#define GROUND_STATION_PORT 8080
```

> [!NOTE]
> `config.h` is ignored by Git in `.gitignore` to prevent leaking private wireless credentials.

### Step 2: Build & Flash Drone Controller
Connect the drone's ESP32 module via USB:
```bash
cd firmware/drone_controller
pio run -t upload
pio device monitor -b 115200
```

### Step 3: Build & Flash Remote Transmitter
Connect the secondary ESP32 remote transmitter module:
```bash
cd ../remote_controller
pio run -t upload
```

---

## 4. Running the Ground Station Application

### Stream Receiver & Preprocessing Pipeline
To launch the real-time ground receiver and inference pipeline:
```bash
# Activate virtual environment
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows

# Launch ground station worker
python scripts/run_ground_station.py --mode plan_a --port 8080
```

### Command-line Arguments
- `--mode`: `plan_a` (Camouflage/Anomaly detection) or `plan_b` (Person detection & tracking fallback).
- `--source`: Network port (`8080`) or local video/file path for bench replay testing.
- `--save-annotated`: Save marked frames to `ground_station/results/`.
- `--enable-heatmap`: Generate and display confidence anomaly heatmaps.

### Offline Testing Without Live Drone
To validate the computer-vision and model pipeline without a live drone connected:
```bash
python scripts/test_stream.py --synthetic
```
This utility streams synthetic terrain images with blended camouflaged patterns through the local socket to verify receiver performance and latency metrics.
