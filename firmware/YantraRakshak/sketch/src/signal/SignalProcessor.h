#ifndef YANTRA_RAKSHAK_SIGNAL_PROCESSOR_H
#define YANTRA_RAKSHAK_SIGNAL_PROCESSOR_H

#include <Arduino.h>

#include "../config/Config.h"
#include "../sensors/MPU6050Sensor.h"

// Converts a completed vibration window into the fused, fixed-length
// feature vector the TinyML model expects. This is the only module that
// turns raw sensor samples into model input.
//
// The feature set (mean, rms, peak, crestFactor, kurtosis of the 3-axis
// acceleration magnitude signal) and the standardization constants below
// are not placeholders -- they were derived from training a real
// autoencoder on real CWRU Bearing Data Center recordings. See
// docs/MODEL_TRAINING_REPORT.md for the full methodology, and
// machine-learning/training/train_autoencoder.py to regenerate both the
// model and these constants together if retrained.
class SignalProcessor {
public:
    static constexpr uint8_t kFeatureCount = MlConfig::kFeatureVectorLength;

    SignalProcessor();

    // Computes the fused feature vector from a vibration window (length
    // SamplingConfig::kWindowSize), writing kFeatureCount floats into
    // outFeatures (caller-owned, must hold at least kFeatureCount
    // elements). The output is already standardized (z-scored) against the
    // trained model's expected input distribution.
    void extractFeatures(const MPU6050Sensor::Sample* vibrationWindow, size_t vibrationCount,
                          float* outFeatures);

private:
    float magnitudeScratch_[SamplingConfig::kWindowSize];

    static void computeMagnitudeStats(const float* samples, size_t count,
                                       float& outMean, float& outRms, float& outPeak,
                                       float& outCrestFactor, float& outKurtosis);
    static void applyStandardization(float* features, uint8_t count);
};

#endif // YANTRA_RAKSHAK_SIGNAL_PROCESSOR_H
