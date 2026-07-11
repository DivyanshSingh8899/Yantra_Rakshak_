#include "SensorManager.h"

#include "../utils/Logger.h"

SensorManager::SensorManager()
    : lastVibrationSampleMs_(0),
      vibrationIntervalMs_(1000UL / SamplingConfig::kVibrationSampleRateHz) {}

bool SensorManager::begin() {
    const bool vibrationOk = mpuSensor_.begin();

    if (!vibrationOk) {
        Logger::error("SensorManager", "Vibration sensor unavailable; continuing in degraded mode");
    }

    lastVibrationSampleMs_ = millis();

    return vibrationOk;
}

void SensorManager::update() {
    const uint32_t now = millis();

    if (mpuSensor_.isHealthy() && (now - lastVibrationSampleMs_) >= vibrationIntervalMs_) {
        lastVibrationSampleMs_ = now;

        MPU6050Sensor::Sample sample;
        if (mpuSensor_.read(sample)) {
            vibrationBuffer_.push(sample);
        }
    }
}

bool SensorManager::isVibrationHealthy() const {
    return mpuSensor_.isHealthy();
}

CircularBuffer<MPU6050Sensor::Sample, SamplingConfig::kVibrationBufferCapacity>& SensorManager::vibrationBuffer() {
    return vibrationBuffer_;
}
