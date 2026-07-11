#ifndef YANTRA_RAKSHAK_MPU6050_SENSOR_H
#define YANTRA_RAKSHAK_MPU6050_SENSOR_H

#include <Adafruit_MPU6050.h>
#include <Arduino.h>

// Owns I2C communication with the MPU6050. Produces calibrated vibration
// samples (acceleration + angular rate) relative to the at-rest baseline
// recorded during begin() -- so downstream processing sees deviation from
// the machine's installed resting state rather than raw absolute readings.
class MPU6050Sensor {
public:
    struct Sample {
        uint32_t timestampMs;
        float accelX;
        float accelY;
        float accelZ;
        float gyroX;
        float gyroY;
        float gyroZ;
    };

    MPU6050Sensor();

    // Initializes the sensor over I2C, configures its range/filter, and runs
    // the at-rest zero-offset calibration. Returns false if the sensor
    // could not be found on the bus.
    bool begin();

    // True if the sensor is currently responding correctly.
    bool isHealthy() const;

    // Reads one calibrated sample. Returns false (outSample left
    // unmodified) if the sensor is unhealthy or the read fails.
    bool read(Sample& outSample);

private:
    Adafruit_MPU6050 mpu_;
    bool healthy_;

    float accelOffsetX_;
    float accelOffsetY_;
    float accelOffsetZ_;
    float gyroOffsetX_;
    float gyroOffsetY_;
    float gyroOffsetZ_;

    void calibrateOffsets();
    static mpu6050_accel_range_t mapAccelRange(uint8_t rangeG);
};

#endif // YANTRA_RAKSHAK_MPU6050_SENSOR_H
