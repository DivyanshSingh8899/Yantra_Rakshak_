// Sourced from docs/WIRING_DIAGRAM.md -- keep in sync with
// firmware/YantraRakshak/sketch/src/config/Config.h if pins ever change.

export const BOARD_PINS = [
  { id: "uno-3v3", label: "3.3V", x: 150, y: 90 },
  { id: "uno-gnd-1", label: "GND", x: 150, y: 120 },
  { id: "uno-scl", label: "SCL", x: 150, y: 150 },
  { id: "uno-sda", label: "SDA", x: 150, y: 180 },
  { id: "uno-d9", label: "D9 (PWM)", x: 150, y: 260 },
  { id: "uno-d10", label: "D10 (PWM)", x: 150, y: 290 },
  { id: "uno-d11", label: "D11 (PWM)", x: 150, y: 320 },
  { id: "uno-gnd-2", label: "GND", x: 150, y: 350 },
];

export const MPU6050_PINS = [
  { id: "mpu-vcc", label: "VCC", x: 470, y: 60 },
  { id: "mpu-gnd", label: "GND", x: 470, y: 90 },
  { id: "mpu-scl", label: "SCL", x: 470, y: 120 },
  { id: "mpu-sda", label: "SDA", x: 470, y: 150 },
  { id: "mpu-ad0", label: "AD0", x: 470, y: 180 },
  { id: "mpu-int", label: "INT", x: 470, y: 210 },
];

export const LED_PINS = [
  { id: "led-r", label: "R", x: 470, y: 270 },
  { id: "led-g", label: "G", x: 470, y: 300 },
  { id: "led-b", label: "B", x: 470, y: 330 },
  { id: "led-gnd", label: "GND", x: 470, y: 360 },
];

export const CONNECTIONS = [
  {
    id: "vcc",
    from: "uno-3v3",
    to: "mpu-vcc",
    color: "#d03b3b",
    label: "3.3V power",
    note: "MPU6050 VCC — STM32U585-managed 3.3V header (JDIGITAL) or Qwiic connector.",
  },
  {
    id: "gnd-mpu",
    from: "uno-gnd-1",
    to: "mpu-gnd",
    color: "#333333",
    label: "Ground",
    note: "Shared ground rail between UNO Q and the MPU6050 breakout.",
  },
  {
    id: "scl",
    from: "uno-scl",
    to: "mpu-scl",
    color: "#3b82d0",
    label: "I2C clock (SCL)",
    note: "I2C clock line, STM32U585-managed.",
  },
  {
    id: "sda",
    from: "uno-sda",
    to: "mpu-sda",
    color: "#0ca35a",
    label: "I2C data (SDA)",
    note: "I2C data line, STM32U585-managed.",
  },
  {
    id: "ad0",
    from: "uno-gnd-1",
    to: "mpu-ad0",
    color: "#333333",
    label: "AD0 → GND",
    note: "Ties AD0 to ground, setting the I2C address to 0x68 (matches Mpu6050Config::kI2cAddress).",
  },
  {
    id: "int",
    from: null,
    to: "mpu-int",
    color: "#c9c8bf",
    label: "INT (not connected)",
    note: "Polling-based reads are used — no interrupt wiring required.",
  },
  {
    id: "led-red",
    from: "uno-d9",
    to: "led-r",
    color: "#d03b3b",
    label: "Red anode",
    note: "Digital pin 9 (PWM) via a 220–330 Ω resistor.",
  },
  {
    id: "led-green",
    from: "uno-d10",
    to: "led-g",
    color: "#0ca30c",
    label: "Green anode",
    note: "Digital pin 10 (PWM) via a 220–330 Ω resistor.",
  },
  {
    id: "led-blue",
    from: "uno-d11",
    to: "led-b",
    color: "#3b82d0",
    label: "Blue anode",
    note: "Digital pin 11 (PWM) via a 220–330 Ω resistor.",
  },
  {
    id: "led-gnd",
    from: "uno-gnd-2",
    to: "led-gnd",
    color: "#333333",
    label: "Common cathode",
    note: "Shared ground rail, common cathode configuration.",
  },
];

export const ALL_PINS = [...BOARD_PINS, ...MPU6050_PINS, ...LED_PINS];
