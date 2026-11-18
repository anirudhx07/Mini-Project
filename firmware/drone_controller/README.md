# SkyForge Onboard Drone Controller Firmware

Target Architecture: ESP32 / ESP32-S3 Dual-Core Microcontroller  
Build Framework: PlatformIO / Arduino C++  

---

## 1. Directory Structure

```
drone_controller/
├── include/
│   ├── config.h.example     # Configuration template (Wi-Fi, Pinouts)
│   └── config.h             # Ignored private settings
├── src/
│   └── main.cpp             # Flight controller initialization & diagnostic loop
├── platformio.ini           # Build environment, board definition & libraries
└── README.md
```

---

## 2. Implementation Status

- [x] **LEDC Motor PWM Channels:** Configured at 20 kHz ultrasonic frequency with 10-bit resolution.
- [x] **Safety Interlock & Disarm:** Firmware zeroes motor registers on boot and supports hardware failsafe disarm.
- [x] **I2C MPU6050 Verification:** Registers polled over 400 kHz Fast-Mode I2C bus.
- [ ] **Closed-Loop PID Flight Loop:** Under development for Week 7 integration.
- [ ] **Camera DMA Acquisition & Wi-Fi Streaming:** Sensor evaluation ongoing.

---

## 3. Build & Flash Instructions

1. Install [PlatformIO Core](https://platformio.org/install/cli) or VS Code extension.
2. Copy `include/config.h.example` to `include/config.h` and configure local parameters.
3. Build and upload:
   ```bash
   pio run -t upload
   pio device monitor -b 115200
   ```
