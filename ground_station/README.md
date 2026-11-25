# COCKPIT — AI-Powered Drone Ground Control Station

**Tagline:** *See. Analyze. Control.*

**COCKPIT** is a local web-based ground control station for monitoring an **ESP32 + MPU6050** flight-controller prototype over Wi-Fi UDP while running modular computer vision and AI analysis on a laptop.

---

## 1. Hardware & Prototype Scope

### Current Breadboard Hardware
- **ESP32 DevKit V1** (30-pin) + **MPU6050 GY-521** (I2C)
- Breadboard, jumper wires, Li-Po battery, TP4056 charger/protection, USB power bank
- **Laptop Webcam** (initial camera source)
- **Laptop GPU:** NVIDIA RTX 4050 (CUDA when PyTorch CUDA is installed; CPU fallback otherwise)

### Future Hardware (Modular Adapter Ready)
- **ESP32-CAM AI Thinker** + **OV2640** + **ESP32-CAM-MB**
- See `backend/camera/esp32cam_source.py` — swap source to `esp32cam` and set stream URL without rebuilding COCKPIT.

> **Safety Scope:** This is a stationary breadboard ground-station prototype. No motor actuation or autonomous flight controls are exposed.

---

## 2. ESP32 USB Serial Telemetry Protocol (Default)

By default, COCKPIT communicates directly with your **ESP32 DevKit V1** over a **USB cable** (`USB_SERIAL` mode at **115200 baud** via Silicon Labs CP210x), while keeping `UDP_WIFI` modular in System Settings.

Both modes expect 8 newline-terminated comma-separated numerical values in this exact order:

```text
ax,ay,az,gx,gy,gz,pitch,roll
```

- `ax, ay, az`: Acceleration ($\text{m/s}^2$)
- `gx, gy, gz`: Angular velocity ($\text{deg/s}$); `gz` is displayed as **Yaw Rate**, not absolute heading
- `pitch, roll`: Calculated orientation angles ($\text{deg}$)
- **Windows Port Rule:** Close **Arduino Serial Monitor** or any other serial tool before clicking **Connect** in COCKPIT, because Windows only allows one process to open a COM port at a time.
- **Connection Timeout:** ESP32 is marked `DISCONNECTED` after 3.0 seconds without valid packets.
- **Mode:** Always starts in **REAL HARDWARE MODE**. **DEMO MODE** is disabled by default and must be toggled explicitly.

---

## 3. Quick Start (Windows)

```powershell
# 1. Install core dependencies
pip install -r ground_station\requirements.txt

# 2. (Optional) Enable RTX 4050 CUDA + YOLO Object Detection & Tracking
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
pip install ultralytics
# Place yolov8n.pt inside ground_station\models\

# 3. Copy environment template if customizing ports/paths
copy ground_station\.env.example ground_station\.env

# 4. Launch COCKPIT
start_cockpit.bat
```

Open **`http://127.0.0.1:5000`** in your browser.

---

## 4. Running Automated Tests

```powershell
cd ground_station
pytest tests/ -v
```
