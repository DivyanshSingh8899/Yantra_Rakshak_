#ifndef YANTRA_RAKSHAK_ANOMALY_DETECTOR_H
#define YANTRA_RAKSHAK_ANOMALY_DETECTOR_H

#include <Arduino.h>
#include <tensorflow/lite/micro/micro_interpreter.h>
#include <tensorflow/lite/micro/micro_mutable_op_resolver.h>

#include "../config/Config.h"

// EXPERIMENTAL / secondary path: runs the same trained model on the MCU
// via TensorFlow Lite Micro. Zephyr does have an official TFLM module
// (confirmed: docs.zephyrproject.org tflite-micro sample, enabled through
// Kconfig -- see sketch/prj.conf), but there is no confirmed evidence
// Arduino's arduino:zephyr CLI wrapper exposes that Kconfig path through
// sketch.yaml the way it does Arduino libraries. This class is provided
// for teams who want to test that path on real hardware; the recommended,
// confirmed-working default is Python-side inference in python/main.py
// (see docs/ARDUINO_UNO_Q_API_VERIFICATION.md for the full reasoning).
class AnomalyDetector {
public:
    enum class HealthStatus : uint8_t { kHealthy, kWarning, kCritical };

    struct Result {
        HealthStatus status;
        float anomalyScore;
        float confidence;
        // Index (0-4: mean, rms, peak, crestFactor, kurtosis) of the
        // feature that contributed the largest individual reconstruction
        // error -- a coarse, explainable signal, not a trained classifier.
        uint8_t dominantFeatureIndex;
    };

    AnomalyDetector();

    // Loads the embedded model and allocates the tensor arena. Returns
    // false if the model is invalid or the arena is too small.
    bool begin();

    // Runs inference on a feature vector (length MlConfig::kFeatureVectorLength)
    // and fills outResult. Returns false if inference could not be executed.
    bool infer(const float* features, Result& outResult);

private:
    alignas(16) uint8_t tensorArena_[MlConfig::kTensorArenaSize];

    tflite::MicroMutableOpResolver<2> opResolver_;
    const tflite::Model* model_;
    tflite::MicroInterpreter* interpreter_;

    static HealthStatus classify(float anomalyScore);
};

#endif // YANTRA_RAKSHAK_ANOMALY_DETECTOR_H
