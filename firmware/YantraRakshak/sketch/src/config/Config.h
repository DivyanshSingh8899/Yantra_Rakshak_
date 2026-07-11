#ifndef YANTRA_RAKSHAK_CONFIG_H
#define YANTRA_RAKSHAK_CONFIG_H

#include <Arduino.h>

// ============================================================================
// YantraRakshak MCU (Zephyr sketch) Configuration
//
// Corrected against the official Arduino UNO Q documentation (see
// docs/ARDUINO_UNO_Q_API_VERIFICATION.md for sources). Networking (Wi-Fi,
// MQTT) and TinyML inference are NOT configured here -- confirmed research
// shows Wi-Fi hardware and stack belong to the Qualcomm Linux (MPU) side,
// reached only through the Arduino_RouterBridge RPC bridge, not directly
// from the STM32U585 (Zephyr) MCU sketch. Their configuration lives in
// python/config.py on the MPU side instead.
// ============================================================================

namespace MachineConfig {
    // Unique identifier for the machine this device is mounted on. Also
    // duplicated in python/config.py (MQTT topics/payload) -- the two
    // runtimes are separate build systems and cannot share a header.
    constexpr char kMachineId[] = "Lathe-01";
}

namespace SamplingConfig {
    // Vibration (MPU6050) sampling rate. 500 Hz covers the fundamental and
    // several harmonics of typical industrial motor/bearing vibration bands.
    constexpr uint16_t kVibrationSampleRateHz = 500;

    // Number of samples per analysis window fed to the TinyML model.
    constexpr uint16_t kWindowSize = 128;

    // Circular buffer capacity. Sized to comfortably hold more than one
    // window so a slow consumer never causes a hard overflow before the
    // oldest-sample-drop policy in CircularBuffer kicks in.
    constexpr uint16_t kVibrationBufferCapacity = kWindowSize * 4;
}

namespace Mpu6050Config {
    constexpr uint8_t kI2cAddress = 0x68; // AD0 tied to GND

    // Full-scale accelerometer range. 8g accommodates typical industrial
    // machine vibration amplitude without clipping.
    constexpr uint8_t kAccelRangeG = 8;

    // Number of samples averaged during the at-rest zero-offset calibration
    // routine run once at startup.
    constexpr uint16_t kCalibrationSampleCount = 200;
}

namespace LedConfig {
    // RGB LED channel pins on the STM32U585-managed 3.3V JDIGITAL header
    // (PWM-capable pins). See docs/WIRING_DIAGRAM.md.
    constexpr uint8_t kPinRed   = 9;
    constexpr uint8_t kPinGreen = 10;
    constexpr uint8_t kPinBlue  = 11;

    // Blink period used for the "communication failure" indication.
    constexpr uint32_t kBlinkIntervalMs = 500;

    // Full brightness value for an active channel (0-255 PWM duty cycle).
    constexpr uint8_t kBrightness = 200;
}

namespace MlConfig {
    // Reconstruction-error thresholds the anomaly score is compared
    // against. Calibrated from real CWRU Bearing Data Center recordings --
    // see machine-learning/models/exported/calibration.json and
    // docs/MODEL_TRAINING_REPORT.md for the full methodology and numbers.
    constexpr float kWarningThreshold  = 1.777191f;
    constexpr float kCriticalThreshold = 2.914409f;

    // Tensor arena size for the TensorFlow Lite Micro interpreter (MCU-side
    // experimental inference path only -- see
    // docs/ARDUINO_UNO_Q_API_VERIFICATION.md for why the Python-side path
    // is the recommended default). The trained model is 3264 bytes with a
    // 5-4-2-4-5 dense topology; 8 KB is generous headroom over its actual
    // measured arena usage.
    constexpr uint32_t kTensorArenaSize = 8 * 1024;

    // Feature vector length: mean, rms, peak, crestFactor, kurtosis of the
    // 3-axis acceleration magnitude signal over one window. Reduced from
    // an earlier 32-value design to only what one real MPU6050 channel can
    // honestly support -- see docs/MODEL_TRAINING_REPORT.md.
    constexpr uint8_t kFeatureVectorLength = 5;
}

namespace BridgeConfig {
    // RPC method name the MPU (Python) side registers via Bridge.provide()
    // and the MCU calls via Bridge.call() once per completed window.
    constexpr char kRunInferenceMethod[] = "run_inference";

    // How long the MCU blocks waiting for the Python-side inference result
    // before giving up on updating the LED for that cycle (does not block
    // sampling -- only the LED update for that single window is skipped).
    constexpr uint32_t kRpcTimeoutMs = 2000;
}

#endif // YANTRA_RAKSHAK_CONFIG_H
