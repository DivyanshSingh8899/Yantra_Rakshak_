"""
Offline functional verification for the Python brick's inference logic.

This is NOT a claim of on-hardware verification (no physical UNO Q was
available in this environment). It mocks the two things that only exist on
real hardware/board OS (arduino.app_utils, and an actual reachable MQTT
broker) so the real, non-mocked parts -- model loading, quantize/dequantize
math, classification, JSON payload construction -- can be exercised end to
end against real feature values derived from the same CWRU data used for
training. Run manually: `python test_offline_verification.py`.
"""

import sys
import types
from unittest import mock

# --- Mock the two hardware/OS-only dependencies before importing main ---
fake_app_utils = types.ModuleType("arduino.app_utils")
fake_app_utils.Bridge = mock.MagicMock()
fake_app_utils.App = mock.MagicMock()
fake_arduino_pkg = types.ModuleType("arduino")
fake_arduino_pkg.app_utils = fake_app_utils
sys.modules["arduino"] = fake_arduino_pkg
sys.modules["arduino.app_utils"] = fake_app_utils

with mock.patch("paho.mqtt.client.Client.connect"), \
     mock.patch("paho.mqtt.client.Client.publish"), \
     mock.patch("paho.mqtt.client.Client.loop_start"):
    import main  # noqa: E402  (import after mocking, intentionally)

# A real normal-condition feature vector and a real fault-condition feature
# vector -- these are the ACTUAL standardized output of
# machine-learning/training/train_autoencoder.py's own feature-extraction
# functions run against the first window of 97.mat (normal) and 105.mat
# (fault), using the real calibration.json mean/std. Not hand-guessed.
NORMAL_FEATURES = "0.1654,-0.3189,0.9617,1.3663,0.6162"
FAULT_FEATURES = "1.5153,-7.4070,-5.3964,-2.4126,-2.3116"

print("Testing run_inference() with a real-shaped NORMAL-like feature vector:")
status_normal = main.run_inference(NORMAL_FEATURES)
print(f"  -> status_code={status_normal}, last_payload={main._last_payload}")
assert status_normal in (0, 1, 2), "status code out of range"

print("\nTesting run_inference() with a real-shaped FAULT-like feature vector:")
status_fault = main.run_inference(FAULT_FEATURES)
print(f"  -> status_code={status_fault}, last_payload={main._last_payload}")
assert status_fault in (0, 1, 2), "status code out of range"

assert status_fault > status_normal, (
    "Expected the fault-like vector to score at least as anomalous as the "
    "normal-like vector -- if this fails, the deployed quantized model or "
    "thresholds are inconsistent with training."
)

print("\nAll offline checks passed: model loads, quantize/infer/dequantize "
      "math runs, classification + JSON payload construction work.")
