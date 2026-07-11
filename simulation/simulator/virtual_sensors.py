"""
Virtual Sensors -- produces one realistic multi-sensor reading (RPM,
temperature, voltage, current, vibration X/Y/Z, acoustic level) for a
machine profile deformed by the current (interpolated) scenario effect,
with sensor noise applied per-channel.
"""

import random
from dataclasses import dataclass

from simulator.scenario_engine import MachineProfile, ScenarioEffect
from simulator.sensor_noise_generator import SensorNoiseGenerator


@dataclass
class VirtualSensorReading:
    rpm: float
    temperature_c: float
    voltage_v: float
    current_a: float
    vibration_x_g: float
    vibration_y_g: float
    vibration_z_g: float
    acoustic_db: float


class VirtualSensors:
    def __init__(self, noise_generator: SensorNoiseGenerator | None = None, seed: int | None = None):
        self._noise = noise_generator or SensorNoiseGenerator(seed=seed)
        self._random = random.Random(seed)

    def generate_reading(self, profile: MachineProfile, effect: ScenarioEffect) -> VirtualSensorReading:
        rpm = profile.rpm_baseline
        if effect.rpm_instability > 0:
            rpm += self._random.gauss(0.0, profile.rpm_baseline * effect.rpm_instability)
        rpm = self._noise.rpm_noise(rpm)

        temperature = profile.temperature_baseline_c + effect.temperature_offset_c
        temperature = self._noise.temperature_noise(temperature)

        voltage = self._noise.voltage_noise(profile.voltage_baseline_v)

        current = profile.current_baseline_a * effect.current_multiplier
        current = self._noise.current_noise(current)

        vibration_x = self._noise.vibration_noise(profile.vibration_baseline_g * effect.vibration_x_multiplier)
        vibration_y = self._noise.vibration_noise(profile.vibration_baseline_g * effect.vibration_y_multiplier)
        vibration_z = self._noise.vibration_noise(profile.vibration_baseline_g * effect.vibration_z_multiplier)

        acoustic = profile.acoustic_baseline_db + effect.acoustic_offset_db
        acoustic = self._noise.acoustic_noise(acoustic)

        return VirtualSensorReading(
            rpm=round(rpm, 1),
            temperature_c=round(temperature, 2),
            voltage_v=round(voltage, 1),
            current_a=round(current, 2),
            vibration_x_g=round(vibration_x, 4),
            vibration_y_g=round(vibration_y, 4),
            vibration_z_g=round(vibration_z, 4),
            acoustic_db=round(acoustic, 1),
        )
