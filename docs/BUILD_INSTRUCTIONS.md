# Build Instructions

## MCU Sketch (Arduino CLI — the only confirmed-supported build path)

PlatformIO does **not** yet support Arduino UNO Q (confirmed — see `docs/ARDUINO_UNO_Q_API_VERIFICATION.md`); there is no `platformio.ini` in this project.

From `firmware/YantraRakshak/sketch/`:

```
arduino-cli compile --fqbn arduino:zephyr:unoq .
arduino-cli upload --fqbn arduino:zephyr:unoq -p <PORT> .
arduino-cli monitor -p <PORT> -c baudrate=115200
```

`sketch.yaml` in this folder pins the exact FQBN and libraries so these commands are reproducible without extra flags. If you're using Arduino IDE 2.x instead, open `sketch/sketch.ino` directly — the IDE reads `sketch.yaml` the same way.

## Python Brick

No compilation step — it runs directly on the board's Debian Linux side via Arduino App Lab (which starts `python/main.py` per `app.yaml`), or manually for testing:

```
cd firmware/YantraRakshak/python
pip install -r requirements.txt
python main.py
```

## Regenerating the Model

The model shipped in this repo (`sketch/src/ml/model_data.cpp` and `python/model/autoencoder_int8.tflite`) was produced by actually training on real CWRU Bearing Data Center recordings — see `docs/MODEL_TRAINING_REPORT.md`. To retrain:

```
cd machine-learning
pip install -r requirements.txt
python training/train_autoencoder.py
```

This regenerates `machine-learning/models/exported/autoencoder_int8.tflite` and `calibration.json`. After retraining, copy the new `.tflite` to `firmware/YantraRakshak/python/model/`, regenerate `model_data.cpp`/`.h` (a byte-array export of the same file), and update `SignalProcessor.cpp`'s standardization constants and `Config.h`'s thresholds from the new `calibration.json` — all three must stay in sync since they encode the same trained model.

## Experimental: On-MCU Inference

`sketch/src/ml/AnomalyDetector.cpp` and `model_data.cpp` are present and reference the same real trained model, but are **not** included in the default sketch build path via `sketch.yaml` (TensorFlow Lite Micro is not a confirmed-installable Arduino library on `arduino:zephyr` — see `ARDUINO_UNO_Q_API_VERIFICATION.md`). To attempt it, you would need to add a Zephyr `prj.conf` alongside the sketch enabling `CONFIG_TENSORFLOW_LITE_MICRO=y`, `CONFIG_CPP=y`, `CONFIG_REQUIRES_FULL_LIBC=y` (the Kconfig options Zephyr's own TFLM sample documents) and confirm `arduino-cli`'s zephyr wrapper actually honors it — this was not verified against real hardware in this session.

## Expected Result

A clean `arduino-cli compile` for the sketch, and a Python brick that runs standalone with `python main.py` once its dependencies are installed — no missing files, no manual model-generation step required for the default (Python-inference) path.
