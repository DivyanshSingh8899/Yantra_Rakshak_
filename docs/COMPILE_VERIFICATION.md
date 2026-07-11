# Compile Verification

Real `arduino-cli` install and compile, run in this session — not a claim, a transcript.

## Toolchain Installed (real)

```
$ arduino-cli.exe core list
ID             Installed Latest Name
arduino:avr    1.8.6     1.8.8  Arduino AVR Boards
arduino:zephyr 0.56.0    0.56.0 Arduino UNO Q Board

$ arduino-cli.exe lib list
Name                 Installed Available   Location Description
Arduino_RouterBridge 0.4.2     0.4.3       user     A RPC bridge for Arduino UNO Q boards
Arduino_RPClite      0.3.0     -           user     -
ArxContainer         0.7.0     -           user     -
ArxTypeTraits        0.3.2     -           user     -
DebugLog             0.8.4     -           user     -
MsgPack              0.4.2     -           user     -
Adafruit MPU6050        2.2.9
Adafruit Unified Sensor 1.1.15
Adafruit BusIO          1.17.4
```

The confirmed FQBN (`arduino:zephyr:unoq`) and the confirmed Bridge dependency chain (`Arduino_RouterBridge` -> `Arduino_RPClite` -> `MsgPack`) from `docs/ARDUINO_UNO_Q_API_VERIFICATION.md` matched exactly what `arduino-cli` actually installed — corroborating that research.

## Attempt 1: With the experimental TFLM path inside `sketch/src/` — FAILED (as predicted)

```
$ arduino-cli.exe compile --fqbn arduino:zephyr:unoq .
In file included from .../sketch/src/ml/AnomalyDetector.cpp:1:
.../sketch/src/ml/AnomalyDetector.h:5:10: fatal error: tensorflow/lite/micro/micro_interpreter.h: No such file or directory
    5 | #include <tensorflow/lite/micro/micro_interpreter.h>
      |          ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
compilation terminated.
Error during build: exit status 1
```

This is real, direct confirmation of the caveat raised in `docs/ARDUINO_UNO_Q_API_VERIFICATION.md`: TensorFlow Lite Micro is **not** available through `arduino:zephyr`'s library resolution. The experimental files were moved to `firmware/YantraRakshak/experimental-mcu-inference/` (outside the sketch's build tree) as a direct result of this real failure, not a hypothetical one.

## Attempt 2: Default architecture (Python-side inference) — SUCCEEDED

```
$ arduino-cli.exe compile --fqbn arduino:zephyr:unoq .
Sketch uses 110684 bytes (14%) of program storage space. Maximum is 786432 bytes.
Global variables use 60816 bytes (23%) of dynamic memory, leaving 201328 bytes for local variables. Maximum is 262144 bytes.
```

**The corrected firmware compiles cleanly against the real, officially installed `arduino:zephyr` core**, with no missing files, no manual steps, and 14%/23% flash/RAM utilization.

## Not Verified (no physical board available in this environment)

- Upload/flash to real hardware (`arduino-cli upload`)
- Serial monitor output on a running board
- `Arduino_RouterBridge` RPC round-trip behavior against a live Python brick
- The Python brick's `arduino.app_utils` import (that module ships with the board's own Debian image / Arduino App Lab runtime, not installable standalone on a development machine) — see `docs/PYTHON_VERIFICATION.md` for what *was* checked on the Python side.
