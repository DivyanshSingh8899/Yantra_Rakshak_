# Firmware Architecture (Corrected)

This supersedes the original single-core design after real API verification (`docs/ARDUINO_UNO_Q_API_VERIFICATION.md`) showed Wi-Fi/MQTT and (likely) TinyML inference cannot run directly on the STM32U585/Zephyr MCU sketch the way a classic single-core Arduino board would.

## Module Map

### MCU sketch (`firmware/YantraRakshak/sketch/`, STM32U585 running Arduino sketches over Zephyr OS)

| Module | Responsibility |
|---|---|
| `config/Config.h` | MCU-side tunables: machine ID, sampling rate, MPU6050/LED pins, ML thresholds (real, trained), Bridge RPC config |
| `utils/Logger` | Serial logging |
| `buffer/CircularBuffer<T,N>` | Generic windowed ring buffer |
| `sensors/MPU6050Sensor`, `sensors/SensorManager` | Vibration sensing + scheduling |
| `signal/SignalProcessor` | Raw window -> 5-value real, trained-standardization feature vector |
| `bridge/BridgeRelay` | Wraps `Arduino_RouterBridge`; sends features to Python, receives back a health status code |
| `led/LEDController` | RGB LED status/blink patterns |
| `ml/AnomalyDetector`, `ml/model_data` | **Experimental, not in the default build** — on-MCU inference using the same real trained model, for teams who confirm the Zephyr TFLM Kconfig path works on their toolchain |
| `sketch.ino` | Composition root: sensors -> buffer -> features -> Bridge -> LED |

### Python brick (`firmware/YantraRakshak/python/`, Qualcomm QRB2210 running Debian Linux)

| Module | Responsibility |
|---|---|
| `config.py` | MQTT broker/topic config, machine ID (kept in sync with the sketch's `Config.h`), thresholds |
| `main.py` | Registers `run_inference` for the MCU to call; runs the real trained TFLite model; classifies Healthy/Warning/Critical; builds the JSON payload; publishes to MQTT; returns a status code to the MCU for its LED; periodic heartbeat via `App.run(user_loop=...)` |
| `model/autoencoder_int8.tflite` | The real trained model (see `docs/MODEL_TRAINING_REPORT.md`) |

## Data Flow

```
MPU6050 (I2C)
      |
      v
SensorManager (scheduling, timestamping)
      |
      v
CircularBuffer (vibration, 128-sample windows)
      |
      v
SignalProcessor (mean/rms/peak/crestFactor/kurtosis of accel magnitude, standardized)
      |
      v  [5-value feature vector]
BridgeRelay.sendFeaturesAndGetStatus()  --Bridge.call("run_inference", csv)-->
                                                                                Python: run_inference()
                                                                                  -> TFLite interpreter (real model)
                                                                                  -> reconstruction error / classification
                                                                                  -> JSON payload -> MQTT publish
                                                                                <-- returns status code (0/1/2) --
      <-- LEDController.setMode(...) per returned status
```

## Degraded-Mode Behavior

- Vibration sensor failure: logged, marked unhealthy; `SensorManager` stops feeding the buffer; no Bridge calls happen until it recovers.
- Bridge/Python-side unavailable or timed out: `BridgeRelay` returns `kUnavailable`; LED goes to blinking-red comm-failure state; sampling continues uninterrupted (never blocks on a hung RPC).
- MQTT/Wi-Fi failure: entirely a Python-side concern now; the MCU only sees it indirectly as an RPC failure if the Python process itself is down, not as a direct network state.

## Why This Split (Recap)

Confirmed via official documentation and hardware forum reports (`docs/ARDUINO_UNO_Q_API_VERIFICATION.md`):
1. Wi-Fi hardware and stack belong to the Linux/MPU side.
2. I2S pins for a microphone like the INMP441 are not exposed on this board's headers.
3. TensorFlow Lite Micro on the Zephyr MCU core is a real Zephyr feature but not confirmed reachable through Arduino's CLI tooling, while Python-side TFLite (pip-installable, and the same deployment pattern Edge Impulse itself uses on this exact board) is confirmed and simple.

This is also, not coincidentally, close to the *original* two-core architecture designed earlier in this project (before an intermediate step temporarily collapsed everything into one monolithic MCU sketch) — the real hardware constraints ended up validating that original split.
