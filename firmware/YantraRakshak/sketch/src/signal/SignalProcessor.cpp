#include "SignalProcessor.h"

#include <math.h>

namespace {

// Per-feature standardization constants (mean, standard deviation), copied
// verbatim from machine-learning/models/exported/calibration.json --
// produced by actually training on real CWRU Bearing Data Center
// recordings (machine-learning/training/train_autoencoder.py). Order must
// match the feature layout below: mean, rms, peak, crestFactor, kurtosis.
constexpr float kFeatureMean[SignalProcessor::kFeatureCount] = {
    0.01248929f, 0.03596297f, 0.09797009f, 2.72740507f, -0.20431967f
};

constexpr float kFeatureStdDev[SignalProcessor::kFeatureCount] = {
    0.00194818f, 0.00301559f, 0.01320491f, 0.31797054f, 0.36474171f
};

} // namespace

SignalProcessor::SignalProcessor() {}

void SignalProcessor::extractFeatures(const MPU6050Sensor::Sample* vibrationWindow, size_t vibrationCount,
                                       float* outFeatures) {
    // Combined 3-axis magnitude signal -- orientation-independent overall
    // vibration energy, computed from the already bias/gravity-corrected
    // per-axis readings (see MPU6050Sensor::calibrateOffsets). This is the
    // same physical quantity the training pipeline derives from CWRU's
    // single-channel drive-end accelerometer.
    for (size_t i = 0; i < vibrationCount; i++) {
        const MPU6050Sensor::Sample& s = vibrationWindow[i];
        magnitudeScratch_[i] = sqrtf(s.accelX * s.accelX + s.accelY * s.accelY + s.accelZ * s.accelZ);
    }

    float mean = 0.0f;
    float rms = 0.0f;
    float peak = 0.0f;
    float crestFactor = 0.0f;
    float kurtosis = 0.0f;
    computeMagnitudeStats(magnitudeScratch_, vibrationCount, mean, rms, peak, crestFactor, kurtosis);

    outFeatures[0] = mean;
    outFeatures[1] = rms;
    outFeatures[2] = peak;
    outFeatures[3] = crestFactor;
    outFeatures[4] = kurtosis;

    applyStandardization(outFeatures, kFeatureCount);
}

// Computes mean, rms, peak, crest factor, and kurtosis of the magnitude
// signal over the window -- the exact same five statistics, in the exact
// same order, computed the exact same way (mean subtraction, then
// second/fourth central moments) as
// machine-learning/training/train_autoencoder.py's compute_window_features,
// so the deployed feature vector matches what the model was trained on.
void SignalProcessor::computeMagnitudeStats(const float* samples, size_t count,
                                             float& outMean, float& outRms, float& outPeak,
                                             float& outCrestFactor, float& outKurtosis) {
    float sum = 0.0f;
    for (size_t i = 0; i < count; i++) {
        sum += samples[i];
    }
    const float mean = sum / static_cast<float>(count);

    float sumSquares = 0.0f;
    float sumFourth = 0.0f;
    float peak = 0.0f;
    for (size_t i = 0; i < count; i++) {
        const float centered = samples[i] - mean;
        const float squared = centered * centered;
        sumSquares += squared;
        sumFourth += squared * squared;

        const float absCentered = fabsf(centered);
        if (absCentered > peak) {
            peak = absCentered;
        }
    }

    const float variance = sumSquares / static_cast<float>(count);
    const float rms = sqrtf(variance);
    const float fourthMoment = sumFourth / static_cast<float>(count);

    outMean = mean;
    outRms = rms;
    outPeak = peak;
    outCrestFactor = (rms > 1e-6f) ? (peak / rms) : 0.0f;
    outKurtosis = (variance > 1e-9f) ? (fourthMoment / (variance * variance) - 3.0f) : 0.0f;
}

// Applies the fixed per-feature standardization (z-score) learned from the
// real training set above.
void SignalProcessor::applyStandardization(float* features, uint8_t count) {
    for (uint8_t i = 0; i < count; i++) {
        const float stdDev = (kFeatureStdDev[i] > 1e-6f) ? kFeatureStdDev[i] : 1.0f;
        features[i] = (features[i] - kFeatureMean[i]) / stdDev;
    }
}
