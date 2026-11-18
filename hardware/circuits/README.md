# SkyForge Electronic Circuits & Driver Schematics

## 1. Propulsion Power Stage Architecture

Coreless brushed motors can draw up to 2.5A to 3.5A of stall current at 3.7V. Microcontroller GPIO pins output a maximum of 12mA–40mA at 3.3V. Direct connection will destroy the ESP32.

SkyForge employs discrete low-side N-channel MOSFET switching stages:

```
                  +3.7V Battery Rail
                         |
                         +--------+
                         |        |
                       [Motor]   [D1: Schottky Diode (e.g. 1N5819)]
                         |        | (Cathode to +3.7V, Anode to Drain)
                         +--------+
                         |
                       Drain (D)
   ESP32 GPIO ----+--[Gate (G)]  N-Channel MOSFET (SI2302 / AO3400)
                  |    Source (S)
                [10kΩ]   |
                  |      |
                 GND    GND
```

### Critical Component Roles:
1. **MOSFET (SI2302 / AO3400):** Ultra-low $R_{DS(on)}$ (< 40 mΩ at $V_{GS} = 2.5\text{V}$), capable of handling $I_D \ge 3.5\text{A}$ continuous without heatsinks.
2. **Schottky Flyback Diode (D1):** Clamps high-voltage inductive kickback generated across motor windings when PWM switches off.
3. **10kΩ Gate Pulldown Resistor:** Pulls the gate to ground during microcontroller boot, preventing spurious motor bursts before firmware initialization.

---

## 2. Sensor & Power Conditioning

- **Decoupling Network:** A 100µF low-ESR electrolytic capacitor across the battery terminals filters ripple caused by motor PWM switching.
- **IMU Isolation:** 0.1µF ceramic capacitor placed within 10mm of the MPU6050 VCC pin.
- **I2C Bus:** 4.7kΩ pull-up resistors on SDA (GPIO 21) and SCL (GPIO 22) lines to 3.3V.
