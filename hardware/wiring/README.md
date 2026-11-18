# SkyForge Wiring & Interconnect Specifications

## 1. Pin Mapping & Wire Color Coding

To simplify field maintenance and bench debugging, adhere strictly to standardized wiring colors:

| Subsystem | Wire Color | Signal Description | Connected Pins |
|:---|:---:|:---|:---|
| **Power** | Red | +3.7V Raw Battery Rail | Li-Po Connector (+) to Motor Anodes & Regulator IN |
| **Ground** | Black | System Common Ground | Li-Po (-), ESP32 GND, MOSFET Sources, Sensor GND |
| **Logic VCC** | Orange | Regulated +3.3V Logic | LDO OUT to ESP32 3V3, MPU6050 VCC |
| **I2C SDA** | Green | Serial Data | ESP32 GPIO 21 to MPU6050 SDA |
| **I2C SCL** | Yellow | Serial Clock | ESP32 GPIO 22 to MPU6050 SCL |
| **Motor 1 PWM** | Blue | Front-Left Motor Gate | ESP32 GPIO 25 to MOSFET 1 Gate |
| **Motor 2 PWM** | Blue | Front-Right Motor Gate | ESP32 GPIO 26 to MOSFET 2 Gate |
| **Motor 3 PWM** | Blue | Rear-Right Motor Gate | ESP32 GPIO 27 to MOSFET 3 Gate |
| **Motor 4 PWM** | Blue | Rear-Left Motor Gate | ESP32 GPIO 14 to MOSFET 4 Gate |

---

## 2. Motor Spin Orientation Diagram

```
                FRONT (Camera)
                  ▲
       [M1: CW]       [M2: CCW]
           \             /
            \   [BAY]   /
             \         /
       [M4: CCW]      [M3: CW]
                  ▼
                 REAR
```

- **M1 (Front-Left):** Clockwise (CW) rotation, fitted with CW propeller.
- **M2 (Front-Right):** Counter-Clockwise (CCW) rotation, fitted with CCW propeller.
- **M3 (Rear-Right):** Clockwise (CW) rotation, fitted with CW propeller.
- **M4 (Rear-Left):** Counter-Clockwise (CCW) rotation, fitted with CCW propeller.
