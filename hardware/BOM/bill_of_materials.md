# SkyForge Bill of Materials (BOM)

Comprehensive schedule of parts, components, and laboratory tools for the SkyForge research prototype.

## 1. Electronics & Propulsion Schedule

| Part # | Description | Model / Part Ref | Qty | Target Specification | Status |
|:---:|:---|:---|:---:|:---|:---:|
| E-01 | Microcontroller (Drone) | ESP32-WROOM-32 / ESP32-S3 | 1 | Dual Core, 240MHz, 2.4GHz Wi-Fi/BLE | Selected |
| E-02 | Microcontroller (Remote) | ESP32-WROOM-32 | 1 | Remote transmitter with ESP-NOW | Selected |
| E-03 | 6-DoF Inertial Sensor | InvenSense MPU6050 | 1 | I2C Gyro + Accelerometer breakout | Selected |
| E-04 | Coreless Brushed Motors | 8520 / 720 / 716 Coreless | 4 | 50,000+ RPM @ 3.7V (2x CW, 2x CCW) | Sizing in progress |
| E-05 | Micro Drone Propellers | 55mm – 65mm Props | 4–8 | Matched CW / CCW pairs | Sizing in progress |
| E-06 | Motor Driver Stages | SI2302 / AO3400 N-MOSFET | 4 | $I_D \ge 3.5\text{A}$, $V_{DS} \ge 20\text{V}$, SOT-23 | Specified |
| E-07 | Flyback Protection Diodes | 1N5819 / SS14 Schottky | 4 | Fast recovery, $V_R \ge 20\text{V}$, $I_F \ge 1\text{A}$ | Specified |
| E-08 | Primary Flight Battery | 1S 3.7V Li-Po Cell | 1–2 | 380–500 mAh, $\ge 25\text{C}$ discharge | Sizing in progress |
| E-09 | Camera Module | OV2640 / DVP Interface | 1 | 2MP CMOS sensor, low-weight flex cable | Under evaluation |
| E-10 | Remote Joysticks | 2-Axis Analog Potentiometer | 2 | 10kΩ dual-axis with return-to-center | Selected |
| E-11 | Passive Buzzer & LEDs | 3.3V Micro Buzzer + 0805 LEDs | 2–4 | System state, arming & low-battery | Specified |
| E-12 | 3D Printed Frame | `drone_frame_approx.stl` | 1 | 120mm diagonal, 3.0mm thickness | Modeled |

---

## 2. Laboratory Workshop Tools Schedule

| Tool Category | Equipment | Priority | Purpose |
|:---|:---|:---:|:---|
| **Assembly** | Temperature-controlled Soldering Iron | Essential | Circuit fabrication and motor wiring |
| **Assembly** | 60/40 or Lead-Free Solder Wire + Rosin Flux | Essential | Clean solder joints |
| **Inspection** | Digital Multimeter (DMM) with continuity beeper | Essential | Short-circuit and voltage verification |
| **Safety** | Fireproof Li-Po Charging Bag & Safety Glasses | Essential | Hazard protection during charging & testing |
| **Fabrication** | FDM 3D Printer (PETG / Carbon-PLA capable) | Essential | Frame structure printing |
| **Measurement** | Precision Jewelry Scale (0.01 g resolution) | Strongly Recommended | Aircraft all-up-weight (AUW) auditing |
