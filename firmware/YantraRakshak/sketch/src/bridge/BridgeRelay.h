#ifndef YANTRA_RAKSHAK_BRIDGE_RELAY_H
#define YANTRA_RAKSHAK_BRIDGE_RELAY_H

#include <Arduino.h>

// Wraps Arduino_RouterBridge (the confirmed, officially documented MCU<->MPU
// RPC mechanism -- see docs/ARDUINO_UNO_Q_API_VERIFICATION.md) so the rest
// of the MCU sketch never touches the Bridge API directly. Sends the
// extracted feature vector to the Python side, which runs inference,
// publishes MQTT, and returns a coarse health status code for the LED.
class BridgeRelay {
public:
    enum class RelayStatus : uint8_t { kHealthy = 0, kWarning = 1, kCritical = 2, kUnavailable = 3 };

    BridgeRelay();

    // Registers the Bridge connection. Call once from setup().
    void begin();

    // Serializes the feature vector as a comma-separated string and calls
    // the Python-side "run_inference" method, blocking up to
    // BridgeConfig::kRpcTimeoutMs for a reply. Returns kUnavailable
    // (rather than blocking indefinitely or crashing) if the MPU side does
    // not respond in time -- the sampling loop is never held hostage by a
    // slow or restarting Python process.
    RelayStatus sendFeaturesAndGetStatus(const float* features, uint8_t featureCount);

private:
    static RelayStatus codeToStatus(int32_t code);
};

#endif // YANTRA_RAKSHAK_BRIDGE_RELAY_H
