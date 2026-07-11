# Python Brick — Offline Functional Verification

`arduino.app_utils` (the `Bridge`/`App` objects) only exists on the UNO Q's own Debian image / Arduino App Lab runtime — it cannot be installed or genuinely tested on a development machine. Rather than skip verification of everything else, `python/test_offline_verification.py` mocks only that module (and the network calls in `paho-mqtt`) and exercises every real code path: model loading, INT8 quantize/infer/dequantize math, classification thresholds, fault labeling, and JSON payload construction.

## Test Vectors Used

Not hand-guessed — both are the actual standardized output of `machine-learning/training/train_autoencoder.py`'s own `compute_window_features()` run against real recordings, using the real `calibration.json` mean/std:

| Vector | Source | Values |
|---|---|---|
| "Normal" | first window of `97.mat` (real normal baseline) | `0.1654,-0.3189,0.9617,1.3663,0.6162` |
| "Fault" | first window of `105.mat` (real inner-race fault, held out from training) | `1.5153,-7.4070,-5.3964,-2.4126,-2.3116` |

## Result (actual output, this session)

```
Testing run_inference() with a real-shaped NORMAL-like feature vector:
  -> status_code=0, last_payload={'machine_id': 'Lathe-01', 'timestamp': '...', 'health': 'Healthy', 'fault': 'None', 'confidence': 0.9477, 'anomaly_score': 0.0929}

Testing run_inference() with a real-shaped FAULT-like feature vector:
  -> status_code=2, last_payload={'machine_id': 'Lathe-01', 'timestamp': '...', 'health': 'Critical', 'fault': 'Bearing Fault Signature (rms-dominant)', 'confidence': 1.0, 'anomaly_score': 17.3663}

All offline checks passed: model loads, quantize/infer/dequantize math runs, classification + JSON payload construction work.
```

The real normal window scored 0.093 (well under the 1.777 warning threshold); the real fault window scored 17.37 (Critical, confidence 1.0) — consistent with the training report's measured separation (Section 5 of `docs/MODEL_TRAINING_REPORT.md`: normal mean 0.64, fault mean 17.65).

## What This Does and Doesn't Prove

**Proven**: the Python-side inference/classification/payload logic is correct and consistent with the trained model, independent of the MCU or Bridge.

**Not proven** (no physical board in this environment): the real `Bridge.provide()`/`Bridge.call()` RPC round-trip between the compiled MCU sketch and this Python process, and the `arduino.app_utils` import itself. These require running on real UNO Q hardware.
