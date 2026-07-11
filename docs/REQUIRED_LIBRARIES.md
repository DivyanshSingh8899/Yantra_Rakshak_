# Required Libraries

## MCU sketch (`firmware/YantraRakshak/sketch/`)

Declared in `sketch/sketch.yaml` (Arduino CLI resolves these automatically on `arduino-cli compile`/`upload` — no manual Library Manager step needed for the sketch itself):

| Library | Purpose |
|---|---|
| Adafruit MPU6050 | MPU6050 vibration sensor driver |
| Adafruit Unified Sensor | dependency of Adafruit MPU6050 |
| Adafruit BusIO | dependency of Adafruit MPU6050 |
| Arduino_RouterBridge | official MCU<->MPU RPC bridge (confirmed API — see `docs/ARDUINO_UNO_Q_API_VERIFICATION.md`) |

**Removed from the original list** (confirmed unsupported/unnecessary on this board's real architecture):
- ~~I2S~~ — I2S pins not exposed on UNO Q headers; INMP441 removed
- ~~PubSubClient~~ — MQTT now runs on the Python/Linux side
- ~~ArduinoJson~~ — JSON payload building moved to Python (`json` stdlib)
- ~~NTPClient~~ — timestamps now come from the Linux side's own synced system clock
- ~~WiFi~~ — Wi-Fi is a Linux-side (Debian OS) concern, not a sketch library

**Experimental, not in the default build**: TensorFlow Lite Micro / CMSIS-NN for the optional on-MCU inference path (`AnomalyDetector.cpp`). Not listed in `sketch.yaml` because there is no confirmed Arduino Library Manager package for it on `arduino:zephyr` — see `docs/ARDUINO_UNO_Q_API_VERIFICATION.md` for what would be required (Zephyr Kconfig) to try it.

## Board package

```
arduino-cli core install arduino:zephyr
```
Confirmed FQBN: `arduino:zephyr:unoq`.

## Python brick (`firmware/YantraRakshak/python/`)

Declared in `python/requirements.txt`:

| Package | Purpose |
|---|---|
| tflite-runtime (or tensorflow as fallback) | loads and runs `model/autoencoder_int8.tflite` |
| numpy | feature array handling, quantize/dequantize math |
| paho-mqtt | MQTT publishing to the broker on the Windows laptop |

`arduino.app_utils` (providing `Bridge` and `App`) ships with the UNO Q's Debian image / Arduino App Lab environment — it is not a pip package to install separately.
