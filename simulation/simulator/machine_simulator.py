"""
Machine Simulator -- orchestrates one simulated machine: holds its profile,
current scenario/fault progression, and produces one complete tick
(raw virtual sensor reading + derived health state) on demand.

The raw sensor reading (RPM, temperature, voltage, current, vibration
X/Y/Z, acoustic level) is generated and available for observability/future
use, but only health/fault/confidence/anomaly_score are published to MQTT
-- that's the subset the real Arduino firmware's JSON schema defines, and
matching it exactly is what lets the backend stay unmodified.
"""

from dataclasses import dataclass

from simulator.fault_generator import FaultGenerator
from simulator.health_state_generator import HealthState, HealthStateGenerator
from simulator.scenario_engine import get_machine_profile, get_scenario_effect, interpolate_effect
from simulator.virtual_sensors import VirtualSensorReading, VirtualSensors


@dataclass
class SimulationTick:
    machine_id: str
    reading: VirtualSensorReading
    health_state: HealthState


class MachineSimulator:
    def __init__(self, machine_id: str, machine_type: str, scenario: str = "healthy", seed: int | None = None):
        self.machine_id = machine_id
        self.machine_type = machine_type
        self._profile = get_machine_profile(machine_type)
        self._fault_generator = FaultGenerator()
        self._fault_generator.set_scenario(scenario)
        self._virtual_sensors = VirtualSensors(seed=seed)
        self._health_generator = HealthStateGenerator(seed=seed)

    @property
    def scenario(self) -> str:
        return self._fault_generator.scenario

    def set_scenario(self, scenario: str, injected: bool = False) -> None:
        self._fault_generator.set_scenario(scenario, injected=injected)

    def tick(self, speed_multiplier: float = 1.0) -> SimulationTick:
        intensity = self._fault_generator.get_intensity(speed_multiplier)
        effect = interpolate_effect(get_scenario_effect(self._fault_generator.scenario), intensity)
        reading = self._virtual_sensors.generate_reading(self._profile, effect)
        health_state = self._health_generator.generate(self._fault_generator.scenario, intensity)
        return SimulationTick(machine_id=self.machine_id, reading=reading, health_state=health_state)
