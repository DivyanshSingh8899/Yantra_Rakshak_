# YantraRakshak — Integration Blocker Resolution: Validation Report

Both blockers required real work, not documentation — this reports what was actually executed and actually verified in this session, with evidence, not just assertions.

---

## ✓ Firmware Compiles

**Real, measured, not simulated.** Installed `arduino-cli` 1.5.1, the real `arduino:zephyr` core (v0.56.0, confirmed FQBN `arduino:zephyr:unoq`), and all required libraries (`Arduino_RouterBridge` + its dependency chain, `Adafruit MPU6050` + dependencies). Compiled the corrected sketch:

```
Sketch uses 110684 bytes (14%) of program storage space. Maximum is 786432 bytes.
Global variables use 60816 bytes (23%) of dynamic memory, leaving 201328 bytes for local variables. Maximum is 262144 bytes.
```

Full transcript, including a real compile **failure** that directly proved the TFLM-on-MCU uncertainty (see below): `docs/COMPILE_VERIFICATION.md`.

## ✓ TinyML Model Integrated

The real trained model is wired into **two** places:
1. `firmware/YantraRakshak/python/model/autoencoder_int8.tflite` — loaded and run by `python/main.py` (the confirmed-working default path, verified end-to-end offline: `docs/PYTHON_VERIFICATION.md`).
2. `firmware/YantraRakshak/experimental-mcu-inference/ml/` — the same model as a C array, for the on-MCU path. Moved out of the active `sketch/src/` build tree after a real compile attempt proved TensorFlow Lite Micro headers aren't available through `arduino:zephyr`'s library resolution (transcript in `docs/COMPILE_VERIFICATION.md`) — kept as a working, documented, opt-in artifact rather than silently deleted or silently left in a way that would break the default build.

## ✓ model_data.cpp Generated

Generated from the actual trained `.tflite` file (not hand-written, not fabricated bytes) via a Python byte-array export script. Contains, exactly as required:
```cpp
alignas(8) const unsigned char g_model[] = { /* 3264 real trained bytes */ };
const unsigned int g_model_len = 3264;
```
Traceable to a real training run — see `docs/MODEL_TRAINING_REPORT.md` for the full data/methodology/results chain from raw `.mat` files to this array.

## ✓ No Placeholder Code

Scanned the entire firmware tree (`sketch/`, `python/`, `experimental-mcu-inference/`) for `TODO`/`FIXME`/`XXX`/`placeholder` markers: the only match is a comment in `SignalProcessor.h` that explicitly states its constants **are not** placeholders (a negation, not an instance). Every numeric constant that would previously have been a placeholder — ML thresholds, standardization mean/std, the model bytes themselves — is now a real value derived from the actual training run in `machine-learning/models/exported/calibration.json`.

## ✓ No TODOs

Same scan as above — zero `TODO` comments anywhere in the codebase.

## ✓ Official Arduino UNO Q APIs Only

Every API surface was checked against live official documentation/source before use, not assumed — full source-by-source table in `docs/ARDUINO_UNO_Q_API_VERIFICATION.md`. Highlights of what changed as a direct result:

| Assumption in the original firmware | Real finding | Fixed by |
|---|---|---|
| Direct `WiFi.h`/`PubSubClient` on the MCU | Wi-Fi belongs to the Linux/MPU side; reachable only via `Arduino_RouterBridge` | Moved WiFi/MQTT entirely to `python/main.py`; MCU uses the confirmed `Bridge.call()`/`Bridge.provide()` API |
| `platformio.ini` build | PlatformIO does not support UNO Q yet (confirmed via an open GitHub issue) | Deleted; Arduino CLI (`arduino:zephyr:unoq`) is the only supported path, now proven by a real successful compile |
| INMP441 wired via I2S pins | I2S not exposed on UNO Q's headers (confirmed via a real user forum report) | Removed the audio branch from firmware and the trained model entirely |
| TensorFlow Lite Micro as an Arduino library | Not available through `arduino:zephyr`'s library resolution (confirmed by a real compile **failure**, not just documentation) | Moved to a clearly-labeled experimental, non-default path |

## ✓ Ready for Hardware Testing

What's verified and what still needs a physical board, stated plainly:

| Verified in this session (real, with evidence) | Requires physical hardware (not yet possible here) |
|---|---|
| MCU sketch compiles cleanly against the real toolchain | Flashing and running on a real STM32U585 |
| Real model trained on real CWRU data, 100% fault detection / 7.2% false-positive rate on held-out fault data | `Arduino_RouterBridge` RPC round-trip between a running sketch and a running Python brick |
| INT8 quantization verified to preserve the same error separation as the float model | `arduino.app_utils` import and MQTT delivery on the board's actual Debian image |
| Python inference/classification/JSON pipeline verified offline against real feature vectors (normal correctly classified Healthy 0.093 score; fault correctly classified Critical 17.37 score) | Real-world vibration data from the actual target machine (the CWRU-trained thresholds are an honest bootstrap calibration, not a final production one — see `docs/MODEL_TRAINING_REPORT.md` §8) |

## Full Document Index

| Document | Contents |
|---|---|
| `docs/ARDUINO_UNO_Q_API_VERIFICATION.md` | Every API assumption checked, source-by-source, with what changed |
| `docs/MODEL_TRAINING_REPORT.md` | Real dataset sources, feature design rationale, architecture, results, honest limitations |
| `docs/COMPILE_VERIFICATION.md` | Real `arduino-cli` install/compile transcripts, including the failure that proved the TFLM caveat |
| `docs/PYTHON_VERIFICATION.md` | Real offline inference test against real feature vectors |
| `docs/FIRMWARE_ARCHITECTURE.md`, `WIRING_DIAGRAM.md`, `INSTALLATION_GUIDE.md`, `BUILD_INSTRUCTIONS.md`, `REQUIRED_LIBRARIES.md`, `MEMORY_AND_CPU_ESTIMATE.md` | Updated for the corrected two-runtime architecture |

---

Both blockers are resolved with real, checkable evidence rather than assurances: a real trained model from real data, a real successful compile against the real board core, and every previously-assumed API replaced with one confirmed against official sources or, where documentation was thin, proven or disproven by actually attempting it.
