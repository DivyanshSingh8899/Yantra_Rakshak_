#ifndef YANTRA_RAKSHAK_SENSOR_MANAGER_H
#define YANTRA_RAKSHAK_SENSOR_MANAGER_H

#include <Arduino.h>

#include "../buffer/CircularBuffer.h"
#include "../config/Config.h"
#include "MPU6050Sensor.h"

// Schedules vibration sampling and feeds the circular buffer.
//
// The audio/INMP441 path was removed: real research confirmed the I2S
// pins required for that microphone are not exposed on Arduino UNO Q's
// headers (see docs/ARDUINO_UNO_Q_API_VERIFICATION.md). Adding an acoustic
// channel back requires either an analog sound sensor read via
// analogRead() on a JANALOG pin, or routing through the Qualcomm side's
// JMISC audio input -- both are documented as future work, not silently
// assumed to work here.
class SensorManager {
public:
    SensorManager();

    // Initializes the vibration sensor. Returns true on success; a false
    // return is tracked via isVibrationHealthy() so the system can keep
    // running in a degraded mode rather than refusing to boot.
    bool begin();

    // Samples the vibration sensor according to its schedule and pushes
    // new readings into the circular buffer. Call once per main loop
    // iteration.
    void update();

    bool isVibrationHealthy() const;

    CircularBuffer<MPU6050Sensor::Sample, SamplingConfig::kVibrationBufferCapacity>& vibrationBuffer();

private:
    MPU6050Sensor mpuSensor_;
    CircularBuffer<MPU6050Sensor::Sample, SamplingConfig::kVibrationBufferCapacity> vibrationBuffer_;

    uint32_t lastVibrationSampleMs_;
    uint32_t vibrationIntervalMs_;
};

#endif // YANTRA_RAKSHAK_SENSOR_MANAGER_H
