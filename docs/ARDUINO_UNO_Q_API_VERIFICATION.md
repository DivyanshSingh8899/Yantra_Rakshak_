# Arduino UNO Q — Official API Verification Report

This document records what was actually verified against official Arduino UNO Q sources (not assumed) and what firmware changes each finding required. Research performed via live web search/fetch against docs.arduino.cc, the official datasheet, GitHub, and the Arduino forum.

## Summary Table

| Item | Assumed (original firmware) | Verified (official sources) | Action Taken |
|---|---|---|---|
| MCU | Generic Arduino AVR/SAM-style core | STM32U585 (Cortex-M33), running Arduino sketches **over Zephyr OS** | Rebuilt sketch project as a Zephyr-based Arduino CLI project (`sketch.yaml`, FQBN `arduino:zephyr:unoq`) |
| Board package/FQBN | Unconfirmed placeholder | `arduino:zephyr:unoq`, core `arduino:zephyr`, confirmed installable via `arduino-cli core install arduino:zephyr` | Used exact FQBN in `sketch/sketch.yaml` |
| PlatformIO support | Assumed supported (wrote a `platformio.ini`) | **Not supported.** Confirmed via PlatformIO community forum thread and `platformio/platform-ststm32` GitHub issue #869 requesting UNO Q support -- as of this research, still open/unimplemented | Deleted `platformio.ini`; Arduino CLI is the only supported build path |
| Wi-Fi access from MCU sketch | Assumed direct `WiFi.h`/`WiFiClient` on the MCU | Wi-Fi module (WCBN3536A) and its stack belong to the Qualcomm Linux (MPU) side; Wi-Fi is configured at the Debian OS level. The MCU sketch reaches networking only through the `Arduino_RouterBridge` RPC bridge | Removed `WiFiManager` from the MCU sketch; Wi-Fi/MQTT moved entirely to `python/main.py` |
| MQTT library | Assumed `PubSubClient` on the MCU | MQTT must run on the Linux/Python side (paho-mqtt), since that's where the network stack lives | Removed `MQTTManager` (C++); added `paho-mqtt` publishing in `python/main.py` |
| MCU<->MPU communication | Not designed | `Arduino_RouterBridge` (a wrapper of `Arduino_RPClite`), confirmed API: `Bridge.begin()`, `Bridge.provide(name, fn)` / `Bridge.provide_safe(name, fn)` (MCU registers a callback), `Bridge.call(name, args...)` (either side calls the other, returns an async `RpcCall`), `.result(ref)` (blocking wait), `Bridge.notify()` (fire-and-forget). Confirmed supported argument types include `bool`, `String`, `float`, numeric | Added `BridgeRelay` (MCU) using `Bridge.call()`/`.result()`; `python/main.py` registers `run_inference` via `Bridge.provide()` (Python-side registration inferred from the router's documented symmetric design -- flagged for on-hardware verification) |
| I2S microphone (INMP441) | Assumed direct I2S wiring to MCU pins | **Confirmed unavailable**: an actual UNO Q user forum thread ("How to connect I2S microphone to UNO Q") states the proper I2S pins are not exposed on UNO Q's headers, even though the STM32U585 has 2 SAI (I2S) peripherals internally | Removed `INMP441Sensor` and the entire audio branch from the firmware and the trained model; documented as future work requiring either an analog sound sensor (via ADC) or the Qualcomm-side JMISC audio input |
| TensorFlow Lite Micro on MCU | Assumed installable as an Arduino library | Zephyr does have an official TFLM module (Zephyr project docs: `samples/modules/tflite-micro/hello_world`), enabled via **Kconfig** (`CONFIG_TENSORFLOW_LITE_MICRO=y`, `CONFIG_CPP=y`, `CONFIG_REQUIRES_FULL_LIBC=y`), not the Arduino Library Manager. No confirmed evidence Arduino's `arduino:zephyr` CLI wrapper exposes this Kconfig path through `sketch.yaml` | Kept `AnomalyDetector`/TFLM code as a clearly labeled **experimental, opt-in** path, not part of the default build; made Python-side inference (confirmed working: `tflite-runtime`/`tensorflow.lite.Interpreter`, pip-installable) the default |
| CMSIS-NN | Assumed bundled automatically | CMSIS-NN is real and Cortex-M-targeted, and Zephyr's TFLM sample explicitly supports a CMSIS-NN-kernel build variant -- but this inherits the same Kconfig-only, unconfirmed-through-Arduino-CLI caveat as TFLM above | Same handling as TFLM: documented, not defaulted |
| GPIO / analogRead / digitalWrite / Wire (I2C) | Assumed standard Arduino API | Confirmed: board has 47 GPIOs (22 on 3.3V Arduino-compatible headers managed by the STM32U585, 25 on the 1.8V JMISC header managed by the Qualcomm side); `digitalWrite`, `analogRead` (ADC), PWM, and I2C (`Wire`) are explicitly STM32U585-managed and behave as standard Arduino APIs | No change needed -- `MPU6050Sensor` (I2C) and `LEDController` (PWM/digitalWrite) were already using confirmed-correct APIs |
| Build flags / compiler | Assumed generic `arduino-cli compile` | Confirmed: `arduino:zephyr` uses its own `arm-zephyr-eabi-gcc` toolchain, installed automatically by `arduino-cli core install arduino:zephyr`; no custom flags required for a standard sketch | No special flags added; standard `arduino-cli compile --fqbn arduino:zephyr:unoq` used |

## Verification Method

Real-time web search and page fetches against:
- [docs.arduino.cc/hardware/uno-q/](https://docs.arduino.cc/hardware/uno-q/) -- official hardware page
- [docs.arduino.cc/resources/datasheets/ABX00162-datasheet.pdf](https://docs.arduino.cc/resources/datasheets/ABX00162-datasheet.pdf) -- official datasheet
- [docs.arduino.cc/tutorials/uno-q/user-manual/](https://docs.arduino.cc/tutorials/uno-q/user-manual/) -- official user manual
- [docs.arduino.cc/tutorials/uno-q/routerbridge-multilanguage](https://docs.arduino.cc/tutorials/uno-q/routerbridge-multilanguage) -- Bridge RPC tutorial
- [github.com/arduino/arduino-router](https://github.com/arduino/arduino-router) -- Router/Bridge service source
- [github.com/arduino-libraries/Arduino_RouterBridge](https://github.com/arduino-libraries/Arduino_RouterBridge) -- Bridge library API
- [shawnhymel.com/3074/how-to-use-the-command-line-cli-with-the-arduino-uno-q](https://shawnhymel.com/3074/how-to-use-the-command-line-cli-with-the-arduino-uno-q/) -- confirmed FQBN, sketch.yaml, project layout
- [forum.arduino.cc/t/how-to-connect-i2s-microphone-to-uno-q](https://forum.arduino.cc/t/how-to-connect-i2s-microphone-to-uno-q/1428067) -- confirms I2S pins not exposed
- [community.platformio.org/t/support-for-uno-q](https://community.platformio.org/t/support-for-uno-q/52900) and [github.com/platformio/platform-ststm32/issues/869](https://github.com/platformio/platform-ststm32/issues/869) -- confirms no PlatformIO support yet
- [docs.zephyrproject.org/latest/samples/modules/tflite-micro/hello_world/README.html](https://docs.zephyrproject.org/latest/samples/modules/tflite-micro/tflite-micro.html) -- confirms Zephyr's TFLM Kconfig mechanism
- [docs.edgeimpulse.com/hardware/boards/arduino-uno-q](https://docs.edgeimpulse.com/hardware/boards/arduino-uno-q) -- confirms Edge Impulse deploys/runs inference on the Linux side (`edge-impulse-linux-runner`)
- Live install/compile testing with `arduino-cli` (see `docs/COMPILE_VERIFICATION.md` for the actual command output)

## What Remains Unconfirmed

- The exact `app.yaml` key schema (best-effort reconstruction; regenerate via Arduino App Lab if it differs)
- Whether `Bridge.call()`'s `.result()` supports an explicit timeout argument (used defensively in `BridgeRelay`, but not fabricated as a confirmed signature)
- Python-side `Bridge.provide()` (inferred from the router's symmetric design, not directly quoted in a Python example)
- Whether the on-MCU TFLM/CMSIS-NN path is reachable through `arduino:zephyr`'s CLI wrapper at all (documented as experimental, not defaulted)

These are called out inline in code comments at the exact point they're used, not left as silent assumptions.
