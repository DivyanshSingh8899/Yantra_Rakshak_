# Memory Usage and CPU Utilization Estimate

Updated for the corrected, real architecture (MCU: sensing + feature extraction only; MPU/Python: inference + MQTT).

## MCU Side — REAL, MEASURED (not estimated)

Actual `arduino-cli compile --fqbn arduino:zephyr:unoq` output against the real installed core (v0.56.0) and the full corrected sketch (MPU6050 driver, SensorManager, CircularBuffer, SignalProcessor, BridgeRelay, LEDController):

```
Sketch uses 110684 bytes (14%) of program storage space. Maximum is 786432 bytes.
Global variables use 60816 bytes (23%) of dynamic memory, leaving 201328 bytes for local variables. Maximum is 262144 bytes.
```

| Resource | Used | Available for this build target | % Used |
|---|---|---|---|
| Flash (program storage) | 110,684 bytes | 786,432 bytes (768 KB) | 14% |
| RAM (global variables) | 60,816 bytes | 262,144 bytes (256 KB) | 23% |

Note: the STM32U585 datasheet lists 2 MB flash / 786 KB SRAM total on the chip, but the `arduino:zephyr:unoq` build target's actual linker-reported budget for user sketches is 768 KB flash / 256 KB RAM (the remainder is reserved for the Zephyr kernel/Bridge infrastructure) — the table above uses the real, measured, relevant number rather than the raw chip datasheet figure. See `docs/COMPILE_VERIFICATION.md` for the full compile transcript.

This is substantially lighter than the original 32-feature, dual-sensor, on-MCU-inference design, since inference, MQTT, and NTP all moved off the MCU.

## Experimental On-MCU Inference Path

`experimental-mcu-inference/ml/` (TFLM + the real trained model) is **excluded from the default sketch build** — confirmed by testing: including it in `sketch/src/` caused a real compile failure (`tensorflow/lite/micro/micro_interpreter.h: No such file or directory`), since no TFLM package is installed/available through `arduino:zephyr`'s library resolution. This is why it lives outside `sketch/src/` rather than merely being un-`#include`d — Arduino's build system compiles every `.cpp` under a sketch's `src/` tree regardless of whether the `.ino` includes it. See `docs/COMPILE_VERIFICATION.md` for the actual failing/passing transcripts of both states.

## MPU Side (Qualcomm QRB2210, Debian Linux — RAM/flash budget is the board's 2/4 GB LPDDR4X and 16/32 GB eMMC, not a meaningful constraint for this workload)

| Component | Approx. Size |
|---|---|
| `autoencoder_int8.tflite` | 3,264 bytes (measured, real) |
| tflite-runtime/tensorflow process | tens of MB (typical Python + TFLite runtime footprint) |
| paho-mqtt client | negligible |

Not a resource-constrained environment the way the MCU is — no meaningful memory budget concern here.

## CPU Utilization

| Task | Where | Frequency | Approx. Cost |
|---|---|---|---|
| Vibration sampling | MCU | 500 Hz | negligible (single I2C transaction) |
| Feature extraction (5 stats over 128 samples) | MCU | every ~256 ms | sub-millisecond, no FFT |
| Bridge RPC round-trip | MCU + MPU | every ~256 ms | dependent on RPC/serialization overhead, not independently measured |
| TFLite inference (5-4-2-4-5 dense autoencoder) | MPU (Python) | every ~256 ms | sub-millisecond on a Cortex-A53-class SoC for a 71-parameter model |
| MQTT publish | MPU (Python) | every ~256 ms (anomalous) / 30 s (heartbeat) | negligible |

The MCU's duty cycle is now dominated by the Bridge RPC round-trip rather than compute, since the model itself is tiny (71 parameters, 3,264-byte quantized file) and inference runs on the comparatively powerful Linux SoC.
