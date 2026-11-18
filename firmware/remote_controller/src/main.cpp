/**
 * @file main.cpp
 * @brief SkyForge Remote Transmitter Controller
 * 
 * Target: Secondary ESP32 Module with 2x Analog Joysticks
 * Protocol: ESP-NOW Low-Latency Protocol
 */

#include <Arduino.h>
#include <esp_now.h>
#include <WiFi.h>

#if __has_include("config.h")
    #include "config.h"
#else
    #include "config.h.example"
#endif

// Packet structure sent over ESP-NOW
typedef struct __attribute__((packed)) {
    uint16_t throttle;  // 0 - 1023
    int16_t  yaw;       // -512 to +512
    int16_t  pitch;     // -512 to +512
    int16_t  roll;      // -512 to +512
    uint8_t  armed;     // 0 = DISARMED, 1 = ARMED
    uint32_t timestamp; // Packet sequence timestamp
} ControlPacket;

ControlPacket txPacket;

void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println("\n[INIT] SkyForge Remote Controller initializing...");

    pinMode(PIN_ARM_SWITCH, INPUT_PULLUP);
    pinMode(PIN_MODE_BUTTON, INPUT_PULLUP);

    WiFi.mode(WIFI_STA);
    WiFi.disconnect();

    if (esp_now_init() == ESP_OK) {
        Serial.println("[OK] ESP-NOW wireless protocol initialized.");
    } else {
        Serial.println("[ERR] ESP-NOW initialization failed.");
    }
}

void loop() {
    // Read analog sticks (12-bit ADC on ESP32: 0 - 4095, mapped to 10-bit: 0 - 1023)
    int rawThrottle = analogRead(PIN_JOY1_THROTTLE);
    int rawYaw      = analogRead(PIN_JOY1_YAW);
    int rawPitch    = analogRead(PIN_JOY2_PITCH);
    int rawRoll     = analogRead(PIN_JOY2_ROLL);

    txPacket.throttle = map(rawThrottle, 0, 4095, 0, 1023);
    txPacket.yaw      = map(rawYaw,      0, 4095, -512, 512);
    txPacket.pitch    = map(rawPitch,    0, 4095, -512, 512);
    txPacket.roll     = map(rawRoll,     0, 4095, -512, 512);
    txPacket.armed    = (digitalRead(PIN_ARM_SWITCH) == LOW) ? 1 : 0;
    txPacket.timestamp = millis();

    // Bench diagnostic print every 250 ms
    static unsigned long lastPrint = 0;
    if (millis() - lastPrint >= 250) {
        lastPrint = millis();
        Serial.printf("[TX] Thr: %4d | Yaw: %4d | Pit: %4d | Rol: %4d | Arm: %d\n",
                      txPacket.throttle, txPacket.yaw, txPacket.pitch, txPacket.roll, txPacket.armed);
    }

    delay(20); // 50 Hz control packet transmission rate
}
