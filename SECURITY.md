# Security Policy — SkyForge

## 1. Scope & Vulnerability Reporting

SkyForge operates an embedded ESP32 microcontroller communicating over 2.4 GHz Wi-Fi and ESP-NOW links with a ground-station processing environment.

If you identify a security issue, vulnerability in wireless packet parsing, or safety flaw in firmware failsafes:
- **Do not open a public issue.**
- Contact the project maintainers via private channels or team members at GLA University.
- Include a reproducible proof of concept and description of potential impact.

---

## 2. Embedded & Wireless Security Guidelines

### Wi-Fi Credential Management
- Never commit hardcoded Wi-Fi passwords, access point credentials, or sensitive network configurations to the repository.
- Use `firmware/**/secrets.h` or environment variables for local configuration. A template `config.h.example` is provided in each firmware module.

### Failsafe Mechanisms
- The drone firmware includes watchdog checks and communication-loss disarm routines.
- If the ground station or remote transmitter loses telemetry connection for more than 500 ms, the flight controller will automatically zero motor PWM to prevent runaway conditions.

### Dataset & Image Privacy
- Test imagery captured during development must not contain unauthorized photos of uninvolved individuals.
- Ground-station logs and captured test frames are stored locally and are excluded from version control via `.gitignore`.
