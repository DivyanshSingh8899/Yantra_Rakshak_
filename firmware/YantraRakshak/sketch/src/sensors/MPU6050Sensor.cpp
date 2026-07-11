#include "MPU6050Sensor.h"

#include "../config/Config.h"
#include "../utils/Logger.h"

MPU6050Sensor::MPU6050Sensor()
    : healthy_(false),
      accelOffsetX_(0.0f), accelOffsetY_(0.0f), accelOffsetZ_(0.0f),
      gyroOffsetX_(0.0f), gyroOffsetY_(0.0f), gyroOffsetZ_(0.0f) {}

bool MPU6050Sensor::begin() {
    if (!mpu_.begin(Mpu6050Config::kI2cAddress)) {
        Logger::error("MPU6050Sensor", "Sensor not found on I2C bus");
        healthy_ = false;
        return false;
    }

    mpu_.setAccelerometerRange(mapAccelRange(Mpu6050Config::kAccelRangeG));
    mpu_.setGyroRange(MPU6050_RANGE_500_DEG);
    // Widest available low-pass filter setting so the passband covers the
    // full vibration spectrum captured at 500 Hz (Nyquist = 250 Hz).
    mpu_.setFilterBandwidth(MPU6050_BAND_260_HZ);

    healthy_ = true;
    calibrateOffsets();

    Logger::info("MPU6050Sensor", "Initialized and calibrated");
    return true;
}

bool MPU6050Sensor::isHealthy() const {
    return healthy_;
}

bool MPU6050Sensor::read(Sample& outSample) {
    if (!healthy_) {
        return false;
    }

    sensors_event_t accelEvent;
    sensors_event_t gyroEvent;
    sensors_event_t tempEvent;

    if (!mpu_.getEvent(&accelEvent, &gyroEvent, &tempEvent)) {
        healthy_ = false;
        Logger::error("MPU6050Sensor", "Read failed; marking sensor unhealthy");
        return false;
    }

    outSample.timestampMs = millis();
    outSample.accelX = accelEvent.acceleration.x - accelOffsetX_;
    outSample.accelY = accelEvent.acceleration.y - accelOffsetY_;
    outSample.accelZ = accelEvent.acceleration.z - accelOffsetZ_;
    outSample.gyroX = gyroEvent.gyro.x - gyroOffsetX_;
    outSample.gyroY = gyroEvent.gyro.y - gyroOffsetY_;
    outSample.gyroZ = gyroEvent.gyro.z - gyroOffsetZ_;

    return true;
}

// Averages a run of at-rest samples to establish the machine's installed
// baseline. Subsequent read() calls report deviation from this baseline
// (including the gravity component) rather than absolute physical units --
// appropriate for vibration monitoring, where only the dynamic deviation
// from the mounted resting state matters.
void MPU6050Sensor::calibrateOffsets() {
    float sumAccelX = 0.0f;
    float sumAccelY = 0.0f;
    float sumAccelZ = 0.0f;
    float sumGyroX = 0.0f;
    float sumGyroY = 0.0f;
    float sumGyroZ = 0.0f;

    sensors_event_t accelEvent;
    sensors_event_t gyroEvent;
    sensors_event_t tempEvent;

    for (uint16_t i = 0; i < Mpu6050Config::kCalibrationSampleCount; i++) {
        mpu_.getEvent(&accelEvent, &gyroEvent, &tempEvent);
        sumAccelX += accelEvent.acceleration.x;
        sumAccelY += accelEvent.acceleration.y;
        sumAccelZ += accelEvent.acceleration.z;
        sumGyroX += gyroEvent.gyro.x;
        sumGyroY += gyroEvent.gyro.y;
        sumGyroZ += gyroEvent.gyro.z;
        delay(2);
    }

    const float sampleCount = static_cast<float>(Mpu6050Config::kCalibrationSampleCount);
    accelOffsetX_ = sumAccelX / sampleCount;
    accelOffsetY_ = sumAccelY / sampleCount;
    accelOffsetZ_ = sumAccelZ / sampleCount;
    gyroOffsetX_ = sumGyroX / sampleCount;
    gyroOffsetY_ = sumGyroY / sampleCount;
    gyroOffsetZ_ = sumGyroZ / sampleCount;
}

mpu6050_accel_range_t MPU6050Sensor::mapAccelRange(uint8_t rangeG) {
    switch (rangeG) {
        case 2:  return MPU6050_RANGE_2_G;
        case 4:  return MPU6050_RANGE_4_G;
        case 8:  return MPU6050_RANGE_8_G;
        case 16: return MPU6050_RANGE_16_G;
        default: return MPU6050_RANGE_8_G;
    }
}
