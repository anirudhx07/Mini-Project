/**
 * @file main.cpp
 * @brief SkyForge / COCKPIT ESP32 DevKit V1 + MPU6050 USB Serial Telemetry Firmware
 *
 * Reads MPU6050 6-axis accelerometer & gyroscope over I2C (Wire.h),
 * computes pitch and roll via complementary filter, and transmits
 * newline-terminated CSV telemetry at 115200 baud for COCKPIT:
 *
 *   ax,ay,az,gx,gy,gz,pitch,roll\n
 *
 * Units:
 *   ax, ay, az   : m/s^2
 *   gx, gy, gz   : deg/s
 *   pitch, roll  : degrees
 *
 * Note: No debug text is printed to Serial so the CSV telemetry stream stays clean.
 */

#include <Arduino.h>
#include <Wire.h>
#include <math.h>

#if __has_include("config.h")
    #include "config.h"
#else
    #include "config.h.example"
#endif

// MPU6050 I2C Address & Registers
static const uint8_t MPU6050_ADDR = 0x68;
static const float GRAVITY_MS2 = 9.80665f;
static const float ACCEL_SCALE_2G = 16384.0f;   // LSB/g for +/-2g range
static const float GYRO_SCALE_250 = 131.0f;     // LSB/(deg/s) for +/-250 deg/s range
static const float RAD_TO_DEG_F = 57.2957795f;

// Sensor & orientation state
float ax = 0.0f, ay = 0.0f, az = 0.0f;
float gx = 0.0f, gy = 0.0f, gz = 0.0f;
float pitch = 0.0f, roll = 0.0f;

bool mpuReady = false;
unsigned long lastSampleMicros = 0;
unsigned long lastTxMillis = 0;
unsigned long lastBlinkMillis = 0;

bool initMPU6050();
bool readMPU6050();

void setup() {
    Serial.begin(115200);
    delay(200);

    pinMode(PIN_STATUS_LED, OUTPUT);
    digitalWrite(PIN_STATUS_LED, LOW);

    // Initialize I2C bus for MPU6050 (GPIO 21 SDA, GPIO 22 SCL @ 400kHz)
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL, 400000);
    mpuReady = initMPU6050();

    lastSampleMicros = micros();
    lastTxMillis = millis();
}

void loop() {
    unsigned long nowMillis = millis();

    // Heartbeat LED: slow blink if waiting for MPU6050, fast blink when streaming
    unsigned long blinkPeriod = mpuReady ? 250 : 1000;
    if (nowMillis - lastBlinkMillis >= blinkPeriod) {
        lastBlinkMillis = nowMillis;
        digitalWrite(PIN_STATUS_LED, !digitalRead(PIN_STATUS_LED));
    }

    if (!mpuReady) {
        static unsigned long lastRetry = 0;
        if (nowMillis - lastRetry >= 1000) {
            lastRetry = nowMillis;
            mpuReady = initMPU6050();
        }
        return;
    }

    // Stream CSV telemetry at 50 Hz (every 20 ms)
    if (nowMillis - lastTxMillis >= 20) {
        lastTxMillis = nowMillis;
        if (readMPU6050()) {
            Serial.printf("%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n",
                          ax, ay, az,
                          gx, gy, gz,
                          pitch, roll);
        }
    }
}

bool initMPU6050() {
    // Verify WHO_AM_I register (0x75)
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(0x75);
    if (Wire.endTransmission(false) != 0) {
        return false;
    }
    Wire.requestFrom(MPU6050_ADDR, (uint8_t)1, (uint8_t)true);
    if (!Wire.available()) {
        return false;
    }
    uint8_t whoami = Wire.read();
    if (whoami != 0x68 && whoami != 0x72) {
        return false;
    }

    // Wake up MPU6050 (PWR_MGMT_1 register 0x6B = 0x00)
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(0x6B);
    Wire.write(0x00);
    if (Wire.endTransmission(true) != 0) {
        return false;
    }

    // Configure accelerometer +/-2g (ACCEL_CONFIG 0x1C = 0x00)
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(0x1C);
    Wire.write(0x00);
    Wire.endTransmission(true);

    // Configure gyroscope +/-250 deg/s (GYRO_CONFIG 0x1B = 0x00)
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(0x1B);
    Wire.write(0x00);
    Wire.endTransmission(true);

    return true;
}

bool readMPU6050() {
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(0x3B); // ACCEL_XOUT_H
    if (Wire.endTransmission(false) != 0) {
        return false;
    }

    Wire.requestFrom(MPU6050_ADDR, (uint8_t)14, (uint8_t)true);
    if (Wire.available() < 14) {
        return false;
    }

    int16_t rawAx = (Wire.read() << 8) | Wire.read();
    int16_t rawAy = (Wire.read() << 8) | Wire.read();
    int16_t rawAz = (Wire.read() << 8) | Wire.read();
    int16_t rawTemp = (Wire.read() << 8) | Wire.read();
    (void)rawTemp;
    int16_t rawGx = (Wire.read() << 8) | Wire.read();
    int16_t rawGy = (Wire.read() << 8) | Wire.read();
    int16_t rawGz = (Wire.read() << 8) | Wire.read();

    // Convert to physical units: m/s^2 and deg/s
    ax = ((float)rawAx / ACCEL_SCALE_2G) * GRAVITY_MS2;
    ay = ((float)rawAy / ACCEL_SCALE_2G) * GRAVITY_MS2;
    az = ((float)rawAz / ACCEL_SCALE_2G) * GRAVITY_MS2;

    gx = (float)rawGx / GYRO_SCALE_250;
    gy = (float)rawGy / GYRO_SCALE_250;
    gz = (float)rawGz / GYRO_SCALE_250;

    unsigned long nowMicros = micros();
    float dt = (float)(nowMicros - lastSampleMicros) / 1000000.0f;
    lastSampleMicros = nowMicros;
    if (dt <= 0.0f || dt > 0.5f) {
        dt = 0.02f;
    }

    // Accelerometer tilt angles in degrees
    float accelPitch = atan2f(-ax, sqrtf(ay * ay + az * az)) * RAD_TO_DEG_F;
    float accelRoll = atan2f(ay, az) * RAD_TO_DEG_F;

    // Complementary filter
    pitch = 0.96f * (pitch + gy * dt) + 0.04f * accelPitch;
    roll  = 0.96f * (roll  + gx * dt) + 0.04f * accelRoll;

    return true;
}
