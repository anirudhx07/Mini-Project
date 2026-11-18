/**
 * @file main.cpp
 * @brief SkyForge Drone Main Controller Firmware
 * 
 * Project: AI-Assisted ESP32 Tiny Drone with Camouflage Image Processing
 * Institution: GLA University, CSE / AIML
 * Team: SkyForge (ID: 87)
 * 
 * IMPLEMENTATION STATUS:
 * [x] Hardware initialization (LEDC PWM motor driver channels, I2C bus)
 * [x] MPU6050 sensor polling & diagnostic orientation readout
 * [x] Telemetry serialization over serial port
 * [x] Emergency motor disarm / safety zero-throttle routine
 * [ ] Full closed-loop 250 Hz PID rate & attitude controller (Under Development)
 * [ ] Camera DMA acquisition & Wi-Fi video streaming (Under Evaluation)
 */

#include <Arduino.h>
#include <Wire.h>

// Attempt to load private config; fallback to defaults if not present
#if __has_include("config.h")
    #include "config.h"
#else
    #include "config.h.example"
#endif

// Motor PWM LEDC Channels
#define CH_M1_FL 0
#define CH_M2_FR 1
#define CH_M3_RR 2
#define CH_M4_RL 3

// System States
enum FlightState {
    STATE_DISARMED = 0,
    STATE_ARMED,
    STATE_FAILSAFE
};

volatile FlightState currentState = STATE_DISARMED;
unsigned long lastHeartbeatTime = 0;
unsigned long lastSensorPollTime = 0;

// Function Declarations
void initMotors();
void setMotorSpeeds(uint16_t m1, uint16_t m2, uint16_t m3, uint16_t m4);
void emergencyDisarm();
bool checkMPU6050();

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n=========================================");
    Serial.println("  SKYFORGE ONBOARD FLIGHT CONTROLLER v1.0");
    Serial.println("  Department of CSE / AIML - GLA University");
    Serial.println("=========================================");

    pinMode(PIN_STATUS_LED, OUTPUT);
    digitalWrite(PIN_STATUS_LED, LOW);

    // 1. Initialize Propulsion Drivers (Safety: Always zero throttle on boot)
    initMotors();
    emergencyDisarm();

    // 2. Initialize I2C Bus for Sensor Diagnostics
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL, 400000); // 400 kHz Fast-Mode
    if (checkMPU6050()) {
        Serial.println("[OK] MPU6050 detected and responding on I2C.");
    } else {
        Serial.println("[WARN] MPU6050 not detected. Verify wiring to GPIO 21/22.");
    }

    Serial.println("[INIT] Baseline hardware initialization complete.");
    Serial.println("[INIT] Motors disarmed. Ready for bench telemetry.");
}

void loop() {
    unsigned long now = millis();

    // Heartbeat LED (1 Hz blink when disarmed, 5 Hz when armed)
    unsigned long blinkInterval = (currentState == STATE_ARMED) ? 100 : 500;
    if (now - lastHeartbeatTime >= blinkInterval) {
        lastHeartbeatTime = now;
        digitalWrite(PIN_STATUS_LED, !digitalRead(PIN_STATUS_LED));
    }

    // Diagnostic Sensor Polling (50 Hz interval)
    if (now - lastSensorPollTime >= 20) {
        lastSensorPollTime = now;

        // Basic I2C acceleration read (Wire register 0x3B)
        Wire.beginTransmission(0x68);
        Wire.write(0x3B);
        if (Wire.endTransmission(false) == 0) {
            Wire.requestFrom(0x68, 6, true);
            if (Wire.available() >= 6) {
                int16_t ax = (Wire.read() << 8) | Wire.read();
                int16_t ay = (Wire.read() << 8) | Wire.read();
                int16_t az = (Wire.read() << 8) | Wire.read();

                // Stream diagnostic orientation data over serial (every 200ms)
                static uint8_t printCounter = 0;
                if (++printCounter >= 10) {
                    printCounter = 0;
                    Serial.printf("[TELEM] IMU Accel -> X: %d | Y: %d | Z: %d | State: %s\n",
                                  ax, ay, az,
                                  (currentState == STATE_DISARMED ? "DISARMED" : "ARMED"));
                }
            }
        }
    }

    // Safety: Handle serial commands for bench testing
    if (Serial.available()) {
        char cmd = (char)Serial.read();
        if (cmd == 'd' || cmd == 'D') {
            emergencyDisarm();
            Serial.println("[CMD] Disarm triggered.");
        } else if (cmd == 's' || cmd == 'S') {
            Serial.println("[CMD] Status report: Safety interlock engaged.");
        }
    }
}

void initMotors() {
    // Configure ESP32 LEDC PWM timers for high-frequency low-noise motor drive
    ledcAttach(PIN_MOTOR_FL_CW, PWM_FREQUENCY, PWM_RESOLUTION);
    ledcAttach(PIN_MOTOR_FR_CCW, PWM_FREQUENCY, PWM_RESOLUTION);
    ledcAttach(PIN_MOTOR_RR_CW, PWM_FREQUENCY, PWM_RESOLUTION);
    ledcAttach(PIN_MOTOR_RL_CCW, PWM_FREQUENCY, PWM_RESOLUTION);
}

void setMotorSpeeds(uint16_t m1, uint16_t m2, uint16_t m3, uint16_t m4) {
    if (currentState != STATE_ARMED) {
        m1 = m2 = m3 = m4 = 0;
    }
    // Cap speeds at safety limit
    m1 = min(m1, (uint16_t)MAX_THROTTLE_LIMIT);
    m2 = min(m2, (uint16_t)MAX_THROTTLE_LIMIT);
    m3 = min(m3, (uint16_t)MAX_THROTTLE_LIMIT);
    m4 = min(m4, (uint16_t)MAX_THROTTLE_LIMIT);

    ledcWrite(PIN_MOTOR_FL_CW, m1);
    ledcWrite(PIN_MOTOR_FR_CCW, m2);
    ledcWrite(PIN_MOTOR_RR_CW, m3);
    ledcWrite(PIN_MOTOR_RL_CCW, m4);
}

void emergencyDisarm() {
    currentState = STATE_DISARMED;
    ledcWrite(PIN_MOTOR_FL_CW, 0);
    ledcWrite(PIN_MOTOR_FR_CCW, 0);
    ledcWrite(PIN_MOTOR_RR_CW, 0);
    ledcWrite(PIN_MOTOR_RL_CCW, 0);
}

bool checkMPU6050() {
    Wire.beginTransmission(0x68);
    Wire.write(0x75); // WHO_AM_I register
    if (Wire.endTransmission(false) != 0) return false;
    Wire.requestFrom(0x68, 1, true);
    if (Wire.available()) {
        uint8_t id = Wire.read();
        return (id == 0x68);
    }
    return false;
}
