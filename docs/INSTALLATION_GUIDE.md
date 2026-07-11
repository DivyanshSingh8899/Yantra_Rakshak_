# Installation Guide

## 1. Set Up the Board (Debian Linux side)

Boot the UNO Q and, per the official user manual, run Arduino App Lab at least once to configure the board and update firmware/packages before using the CLI. Configure Wi-Fi at the OS level (see `kevsrobots.com/blog/arduino-uno-q-wifi-setup.html`-style instructions, or App Lab's own network settings) — Wi-Fi is a Linux-side concern on this board, not something the sketch configures.

## 2. Install arduino-cli and the Board Core (development machine)

```
arduino-cli core update-index
arduino-cli lib update-index
arduino-cli core install arduino:zephyr
```
This installs the confirmed `arduino:zephyr` core (FQBN `arduino:zephyr:unoq`) and its `arm-zephyr-eabi-gcc` toolchain, plus the `Arduino_RouterBridge` library it depends on.

## 3. Wire the Hardware

Follow `WIRING_DIAGRAM.md`. Note the INMP441 microphone is not part of this build (I2S not exposed on this board — see `ARDUINO_UNO_Q_API_VERIFICATION.md`).

## 4. Configure the Sketch

Edit `firmware/YantraRakshak/sketch/src/config/Config.h`:
- `MachineConfig::kMachineId` — must match `python/config.py`'s `MACHINE_ID`

Thresholds and feature configuration already hold real trained values (see `MODEL_TRAINING_REPORT.md`) and don't need to change for a first flash.

## 5. Configure the Python Brick

Edit `firmware/YantraRakshak/python/config.py`:
- `MQTT_BROKER_HOST` — your Windows laptop's LAN IP
- `MACHINE_ID` — must match the sketch's `kMachineId`

Install its dependencies on the board's Linux side:
```
pip install -r python/requirements.txt
```

## 6. Compile and Upload

See `BUILD_INSTRUCTIONS.md`.

## 7. Verify

Serial Monitor (115200 baud) on the MCU side should show:
```
[...ms][INFO][Main] YantraRakshak MCU sketch starting
[...ms][INFO][MPU6050Sensor] Initialized and calibrated
[...ms][INFO][BridgeRelay] Arduino_RouterBridge initialized
[...ms][INFO][Main] Setup complete
```

The Python brick's log (via App Lab or its own stdout) should show the MQTT client connecting and `run_inference` calls arriving once the MCU starts sending 128-sample windows (roughly every 256 ms once both sides are up).

## Nothing Left to Fill In Manually

Unlike the earlier draft of this firmware, there is no missing model file: `sketch/src/ml/model_data.cpp` and `python/model/autoencoder_int8.tflite` both already contain the real trained model (see `MODEL_TRAINING_REPORT.md`). The build should succeed without any additional model-generation step.
