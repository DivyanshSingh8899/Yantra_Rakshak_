#include "src/bridge/BridgeRelay.h"
#include "src/config/Config.h"
#include "src/led/LEDController.h"
#include "src/sensors/SensorManager.h"
#include "src/signal/SignalProcessor.h"
#include "src/utils/Logger.h"

// Composition root for the MCU (STM32U585, running Arduino sketches over
// Zephyr OS) side of Arduino UNO Q.
//
// This sketch deliberately does NOT do Wi-Fi, MQTT, NTP, or on-device
// TinyML inference. Real research against official Arduino UNO Q
// documentation (docs/ARDUINO_UNO_Q_API_VERIFICATION.md) confirmed:
//   - Wi-Fi hardware/stack belongs to the Qualcomm Linux (MPU) side; the
//     MCU reaches it only through the Arduino_RouterBridge RPC bridge.
//   - TensorFlow Lite Micro on this Zephyr-based core is not confirmed to
//     be installable through Arduino's sketch.yaml/Library Manager flow.
// So this sketch's job is real-time sensing + feature extraction + LED
// status; Python/main.py on the Linux side does inference, JSON building,
// and MQTT publishing. See docs/FIRMWARE_ARCHITECTURE.md for the full
// data flow diagram.

SensorManager sensorManager;
SignalProcessor signalProcessor;
BridgeRelay bridgeRelay;
LEDController ledController;

static MPU6050Sensor::Sample vibrationWindow[SamplingConfig::kWindowSize];
static float featureVector[MlConfig::kFeatureVectorLength];

void setup() {
    Logger::begin(115200);
    Logger::info("Main", "YantraRakshak MCU sketch starting");

    ledController.begin();
    bridgeRelay.begin();

    if (!sensorManager.begin()) {
        Logger::error("Main", "Vibration sensor failed to initialize; continuing in degraded mode");
        ledController.setMode(LEDController::Mode::kCommFailure);
    }

    Logger::info("Main", "Setup complete");
}

void loop() {
    sensorManager.update();
    ledController.update();

    CircularBuffer<MPU6050Sensor::Sample, SamplingConfig::kVibrationBufferCapacity>& vibrationBuffer =
        sensorManager.vibrationBuffer();

    if (!vibrationBuffer.isWindowReady(SamplingConfig::kWindowSize)) {
        return;
    }

    vibrationBuffer.consumeWindow(vibrationWindow, SamplingConfig::kWindowSize);
    signalProcessor.extractFeatures(vibrationWindow, SamplingConfig::kWindowSize, featureVector);

    const BridgeRelay::RelayStatus status =
        bridgeRelay.sendFeaturesAndGetStatus(featureVector, MlConfig::kFeatureVectorLength);

    switch (status) {
        case BridgeRelay::RelayStatus::kHealthy:
            ledController.setMode(LEDController::Mode::kHealthy);
            break;
        case BridgeRelay::RelayStatus::kWarning:
            ledController.setMode(LEDController::Mode::kWarning);
            break;
        case BridgeRelay::RelayStatus::kCritical:
            ledController.setMode(LEDController::Mode::kCritical);
            break;
        case BridgeRelay::RelayStatus::kUnavailable:
            ledController.setMode(LEDController::Mode::kCommFailure);
            break;
    }
}
