# SkyForge Remote Transmitter Firmware

Target: Secondary ESP32 Microcontroller  
Protocol: 2.4 GHz ESP-NOW (Low latency, connectionless)  

---

## 1. Overview & Controls

The ground remote transmitter samples two dual-axis analog joystick potentiometers and safety toggle switches at 50 Hz (20 ms interval) and transmits packed telemetry frames to the drone's primary ESP32 receiver.

- **Left Stick (X/Y):** Yaw rate and Throttle.
- **Right Stick (X/Y):** Roll and Pitch angle commands.
- **Safety Arm Switch (Pin 18):** Emergency cut-off and arming interlock.

---

## 2. Configuration & Upload

1. Copy `include/config.h.example` to `include/config.h`.
2. Inspect the drone's Wi-Fi MAC address and update `DRONE_PEER_MAC`.
3. Upload firmware via PlatformIO:
   ```bash
   pio run -t upload
   pio device monitor -b 115200
   ```
