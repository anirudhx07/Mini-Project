# SkyForge Operational Safety & Risk Mitigation Protocols

## 1. Safety Priority Directive

Aerial micro-robotics and experimental lithium-polymer power systems present inherent electrical, fire, and mechanical hazards. Safety protocols must be enforced during every development, flashing, and testing phase.

---

## 2. Lithium-Polymer (Li-Po) Battery Protocol

The prototype utilizes 1S (single-cell) 3.7V Lithium-Polymer batteries with high C-ratings.

| Operational State | Cell Voltage Boundary | Action Required |
|:---|:---:|:---|
| **Full Charge (Max)** | 4.20 V | Terminate charge cycle immediately. Never exceed 4.25 V. |
| **Nominal Operating** | 3.70 V – 3.85 V | Normal flight operating envelope. |
| **Low Voltage Warning** | 3.40 V | Land drone immediately. Battery telemetry alert triggers. |
| **Critical Cut-off (Min)** | 3.20 V | Microcontroller zero-throttles to prevent permanent cell damage. |

### Battery Handling Rules
1. **Dedicated Smart Charger:** Always use a balanced 1S Li-Po charger (e.g., TP4056 with protection IC or commercial micro-drone balanced charger). Never charge with an unregulated DC source.
2. **Charging Supervision:** Never leave charging batteries unattended. Charge only on non-flammable surfaces inside a certified fireproof Li-Po safety bag.
3. **Physical Inspection:** If a cell displays swelling, puncture, excessive heat, or chemical odor, disconnect it immediately, submerge in salt water, and dispose according to regional hazardous waste regulations.

---

## 3. Propeller & Mechanical Injury Mitigation

High-RPM coreless micro-motors spin propellers up to 30,000–50,000 RPM, which can cause lacerations or eye injuries upon unexpected spool-up.

> [!CAUTION]
> **Mandatory Propeller Removal Rule:**
> Propellers **MUST BE REMOVED** at all times during:
> - Firmware flashing and USB debugging.
> - Bench calibration and I2C sensor diagnostics.
> - Motor driver electrical verification.
> - Ground-station network pairing and pipeline calibration.
>
> Propellers are attached **ONLY** during designated enclosed flight trials.

- **Eye Protection:** Safety glasses (ANSI Z87.1 approved) are mandatory for all persons in the testing room during powered propeller tests.
- **Clearance Zone:** Maintain an exclusion radius of at least 3 meters from the drone platform during any tethered hover attempts.

---

## 4. Autonomous Failsafes & Software Guardrails

The drone firmware enforces three independent software failsafes:

1. **Telemetry Loss Watchdog:** If the ESP32 loses heartbeat packets from the ground station or remote transmitter for $> 500\text{ ms}$, the flight controller enters failsafe mode: throttle is ramped down to zero instantly.
2. **Attitude Threshold Cut-Off:** If gyro/accelerometer fusion detects tilt angles exceeding $\pm 45^\circ$ from horizontal (indicating a rollover or aerodynamic stall), motors are killed immediately.
3. **Two-Stage Arming Sequence:** Motors cannot spin on boot. The pilot must explicitly engage an arming switch on the remote transmitter with throttle held at 0%.

---

## 5. Privacy & Ethical Use (Plan B Contingency)

When evaluating Plan B (human subject detection and tracking fallback):
- Test imagery must only feature participating team members or consenting student volunteers.
- Captured frames and evaluation logs are stored strictly on local ground-station storage (`ground_station/results/`) and must never be uploaded to public third-party servers.
- The system is built solely for educational, academic, and open-source scientific evaluation.
