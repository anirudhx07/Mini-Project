# Contributing to SkyForge

Thank you for your interest in contributing to **SkyForge: AI-Assisted ESP32 Tiny Drone with Camouflage Image Processing**! This project unites embedded aerospace engineering, real-time wireless telemetry, and computer vision.

---

## 1. Development Principles

1. **Hardware Safety First:** Never commit code that alters motor PWM safety boundaries or disables failsafes without peer review. Always bench-test firmware modifications without propellers.
2. **Honest Engineering:** Do not commit synthetic benchmark results, simulated flight times, or unverified detection accuracies. Distinguish clearly between tested features and ongoing research.
3. **Modular Subsystems:** Keep firmware flight-stabilization routines strictly isolated from heavier computer-vision workloads. The flight control loop must remain deterministic.

---

## 2. Contribution Workflow

1. **Fork the Repository:** Create a feature branch with a descriptive name:
   ```bash
   git checkout -b feature/cv-clahe-optimization
   # or
   git checkout -b fix/mpu6050-i2c-timeout
   ```
2. **Adhere to Code Standards:**
   - **Firmware (C/C++):** Follow Arduino/PlatformIO standards, modular headers in `include/`, implementations in `src/`.
   - **Ground Station & ML (Python):** PEP 8 compliance, clear docstrings, explicit type annotations where feasible.
   - **CAD/Hardware:** Keep OpenSCAD parameters documented and test 3D sliceability in standard slicers.
3. **Execute Local Validation:**
   ```bash
   pytest tests/
   ```
4. **Submit a Pull Request:**
   - Describe the exact hardware setup used for testing.
   - Attach logs, terminal output, or sample images if introducing vision changes.
   - Reference related project milestones or issues.

---

## 3. Areas Welcoming Contributions

- **Vision Preprocessing:** Optimized contour extraction, adaptive lighting compensation, and texture edge detectors.
- **Embedded Telemetry:** Efficient frame packetization over Wi-Fi UDP/TCP and ESP-NOW remote transmitter ergonomics.
- **AIML Research:** Evaluation on COD10K/CAMO datasets, ONNX runtime conversion, and lightweight person-tracking refinements.
- **Documentation:** Setup guides for different camera sensors, wiring schematics, and test protocols.
