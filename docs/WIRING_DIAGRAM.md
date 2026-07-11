# Wiring Diagram — Arduino UNO Q

Pin assignments match `firmware/YantraRakshak/sketch/src/config/Config.h`. If you change a pin there, update it here too.

**Hardware change from the original design**: the INMP441 (I2S microphone) is **removed**. Real research (an actual UNO Q user forum thread) confirmed the I2S pins required for it are not exposed on UNO Q's headers, even though the STM32U585 MCU has I2S/SAI peripherals internally -- see `docs/ARDUINO_UNO_Q_API_VERIFICATION.md`. The trained model (see `docs/MODEL_TRAINING_REPORT.md`) is vibration-only accordingly. If you want to add an acoustic channel later, the two realistic paths are: (a) an analog sound sensor module read via `analogRead()` on a JANALOG pin, or (b) the Qualcomm side's JMISC audio input (Microphone IN) -- both are future work, not wired in this build.

## MPU6050 (I2C)

| MPU6050 Pin | UNO Q Pin | Notes |
|---|---|---|
| VCC | 3.3V | STM32U585-managed 3.3V header (JDIGITAL) or Qwiic connector |
| GND | GND | shared ground rail |
| SCL | SCL | I2C clock, STM32U585-managed |
| SDA | SDA | I2C data, STM32U585-managed |
| AD0 | GND | sets I2C address to 0x68 (matches `Mpu6050Config::kI2cAddress`) |
| INT | not connected | polling-based reads are used, no interrupt wiring required |

UNO Q has a Qwiic connector for tool-free I2C connections -- if your MPU6050 breakout has a Qwiic/STEMMA QT connector, that's the simplest wiring option and skips the manual SCL/SDA/power wiring above.

## RGB LED (PWM)

| LED Pin | UNO Q Pin | Notes |
|---|---|---|
| Red anode | Digital pin 9 (PWM) | via 220-330 ohm resistor |
| Green anode | Digital pin 10 (PWM) | via 220-330 ohm resistor |
| Blue anode | Digital pin 11 (PWM) | via 220-330 ohm resistor |
| Common cathode | GND | shared ground rail |

Both MPU6050 and the RGB LED are wired to the STM32U585-managed 3.3V Arduino-compatible headers (JDIGITAL/JANALOG/Qwiic) -- not the Qualcomm-side 1.8V JMISC header, which is a separate connector for different peripherals.

## Power

* Development/flashing: USB-C from the laptop is sufficient.
* Sustained operation (Linux side booted, Wi-Fi active, Python brick running): use the board's DC input (7-24V) or a robust USB-C power source -- confirmed via the official UNO Q Power Specifications page that the board supports multiple power inputs; a thin laptop USB port may not sustain the full dual-processor load.

## Before Flashing

Confirm every pin above against the official Arduino UNO Q datasheet (`docs.arduino.cc/resources/datasheets/ABX00162-datasheet.pdf`) and pinout diagram for your specific board revision.
