#include "AnomalyDetector.h"

#include <math.h>
#include <tensorflow/lite/schema/schema_generated.h>

#include "../utils/Logger.h"
#include "model_data.h"

AnomalyDetector::AnomalyDetector()
    : model_(nullptr), interpreter_(nullptr) {}

bool AnomalyDetector::begin() {
    model_ = tflite::GetModel(g_model);

    if (model_->version() != TFLITE_SCHEMA_VERSION) {
        Logger::error("AnomalyDetector", "Model schema version mismatch");
        return false;
    }

    if (opResolver_.AddFullyConnected() != kTfLiteOk) {
        Logger::error("AnomalyDetector", "Failed to register FULLY_CONNECTED op");
        return false;
    }
    if (opResolver_.AddRelu() != kTfLiteOk) {
        Logger::error("AnomalyDetector", "Failed to register RELU op");
        return false;
    }

    static tflite::MicroInterpreter staticInterpreter(
        model_, opResolver_, tensorArena_, MlConfig::kTensorArenaSize);
    interpreter_ = &staticInterpreter;

    if (interpreter_->AllocateTensors() != kTfLiteOk) {
        Logger::error("AnomalyDetector", "Tensor arena allocation failed -- increase kTensorArenaSize");
        interpreter_ = nullptr;
        return false;
    }

    Logger::info("AnomalyDetector", "Model loaded and tensor arena allocated");
    return true;
}

bool AnomalyDetector::infer(const float* features, Result& outResult) {
    if (interpreter_ == nullptr) {
        return false;
    }

    TfLiteTensor* input = interpreter_->input(0);
    TfLiteTensor* output = interpreter_->output(0);

    for (uint8_t i = 0; i < MlConfig::kFeatureVectorLength; i++) {
        const int32_t quantized = static_cast<int32_t>(
            roundf(features[i] / input->params.scale) + input->params.zero_point);
        input->data.int8[i] = static_cast<int8_t>(constrain(quantized, -128, 127));
    }

    if (interpreter_->Invoke() != kTfLiteOk) {
        Logger::error("AnomalyDetector", "Inference invocation failed");
        return false;
    }

    float sumSquaredError = 0.0f;
    float maxSquaredError = 0.0f;
    uint8_t dominantIndex = 0;

    for (uint8_t i = 0; i < MlConfig::kFeatureVectorLength; i++) {
        const float reconstructed =
            (static_cast<int32_t>(output->data.int8[i]) - output->params.zero_point) * output->params.scale;
        const float error = features[i] - reconstructed;
        const float squaredError = error * error;

        sumSquaredError += squaredError;
        if (squaredError > maxSquaredError) {
            maxSquaredError = squaredError;
            dominantIndex = i;
        }
    }

    const float anomalyScore = sumSquaredError / static_cast<float>(MlConfig::kFeatureVectorLength);

    outResult.anomalyScore = anomalyScore;
    outResult.status = classify(anomalyScore);
    outResult.dominantFeatureIndex = dominantIndex;

    switch (outResult.status) {
        case HealthStatus::kHealthy: {
            const float ratio = anomalyScore / MlConfig::kWarningThreshold;
            outResult.confidence = 1.0f - constrain(ratio, 0.0f, 1.0f);
            break;
        }
        case HealthStatus::kWarning: {
            const float span = MlConfig::kCriticalThreshold - MlConfig::kWarningThreshold;
            const float progress = (anomalyScore - MlConfig::kWarningThreshold) / span;
            outResult.confidence = constrain(progress, 0.0f, 1.0f);
            break;
        }
        case HealthStatus::kCritical:
        default: {
            const float ratio = anomalyScore / MlConfig::kCriticalThreshold;
            outResult.confidence = (ratio > 1.0f) ? 1.0f : ratio;
            break;
        }
    }

    return true;
}

AnomalyDetector::HealthStatus AnomalyDetector::classify(float anomalyScore) {
    if (anomalyScore > MlConfig::kCriticalThreshold) {
        return HealthStatus::kCritical;
    }
    if (anomalyScore > MlConfig::kWarningThreshold) {
        return HealthStatus::kWarning;
    }
    return HealthStatus::kHealthy;
}
