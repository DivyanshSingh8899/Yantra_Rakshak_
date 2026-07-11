"""
Sensor Noise Generator -- adds realistic per-sensor Gaussian noise so
simulated readings don't look artificially smooth. Noise magnitudes are
proportional to each sensor's typical measurement precision, not uniform
across sensors (a vibration sensor is noisier, relatively, than a voltage
measurement).
"""

import random


class SensorNoiseGenerator:
    def __init__(self, seed: int | None = None):
        self._random = random.Random(seed)

    def apply(self, value: float, relative_noise_fraction: float, absolute_noise_floor: float = 0.0) -> float:
        """Returns value distorted by Gaussian noise whose standard
        deviation is relative_noise_fraction * |value|, with a minimum
        absolute floor so near-zero values still get some jitter."""
        std_dev = max(abs(value) * relative_noise_fraction, absolute_noise_floor)
        return value + self._random.gauss(0.0, std_dev)

    def rpm_noise(self, value: float) -> float:
        return self.apply(value, relative_noise_fraction=0.003, absolute_noise_floor=1.0)

    def temperature_noise(self, value: float) -> float:
        return self.apply(value, relative_noise_fraction=0.01, absolute_noise_floor=0.2)

    def voltage_noise(self, value: float) -> float:
        return self.apply(value, relative_noise_fraction=0.005, absolute_noise_floor=0.5)

    def current_noise(self, value: float) -> float:
        return self.apply(value, relative_noise_fraction=0.02, absolute_noise_floor=0.05)

    def vibration_noise(self, value: float) -> float:
        return abs(self.apply(value, relative_noise_fraction=0.08, absolute_noise_floor=0.002))

    def acoustic_noise(self, value: float) -> float:
        return self.apply(value, relative_noise_fraction=0.015, absolute_noise_floor=0.3)
