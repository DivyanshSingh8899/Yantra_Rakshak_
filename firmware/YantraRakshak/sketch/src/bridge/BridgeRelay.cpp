#include "BridgeRelay.h"

#include <Arduino_RouterBridge.h>

#include "../config/Config.h"
#include "../utils/Logger.h"

BridgeRelay::BridgeRelay() {}

void BridgeRelay::begin() {
    Bridge.begin();
    Logger::info("BridgeRelay", "Arduino_RouterBridge initialized");
}

BridgeRelay::RelayStatus BridgeRelay::sendFeaturesAndGetStatus(const float* features, uint8_t featureCount) {
    String payload;
    for (uint8_t i = 0; i < featureCount; i++) {
        payload += String(features[i], 6);
        if (i + 1 < featureCount) {
            payload += ",";
        }
    }

    // Bridge.call() is confirmed non-blocking, returning an RpcCall whose
    // .result(ref) blocks for the reply and writes it into ref. The
    // installed Arduino_RouterBridge version's exact timeout behavior on a
    // non-responding Python side was not confirmed against official docs
    // at the time this was written -- if a timeout overload is available,
    // pass BridgeConfig::kRpcTimeoutMs here; verify against the library
    // version actually installed before relying on this in production.
    RpcCall call = Bridge.call(BridgeConfig::kRunInferenceMethod, payload);

    int32_t statusCode = -1;
    if (!call.result(statusCode)) {
        Logger::warn("BridgeRelay", "run_inference RPC failed or timed out");
        return RelayStatus::kUnavailable;
    }

    return codeToStatus(statusCode);
}

BridgeRelay::RelayStatus BridgeRelay::codeToStatus(int32_t code) {
    switch (code) {
        case 0: return RelayStatus::kHealthy;
        case 1: return RelayStatus::kWarning;
        case 2: return RelayStatus::kCritical;
        default: return RelayStatus::kUnavailable;
    }
}
