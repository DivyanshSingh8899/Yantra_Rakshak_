"""
Scenario Engine -- defines the baseline operating envelope for each
supported machine type, and how each supported fault scenario deforms that
baseline as fault intensity ramps from 0 (just starting) to 1 (fully
developed). MachineSimulator consults this every tick; it contains no
timing/threading logic of its own.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MachineProfile:
    machine_type: str
    rpm_baseline: float
    temperature_baseline_c: float
    voltage_baseline_v: float
    current_baseline_a: float
    vibration_baseline_g: float
    acoustic_baseline_db: float


MACHINE_PROFILES: dict[str, MachineProfile] = {
    "electric_motor": MachineProfile("electric_motor", 1465, 55.0, 415.0, 10.0, 0.035, 60.0),
    "water_pump": MachineProfile("water_pump", 2900, 48.0, 415.0, 7.5, 0.05, 65.0),
    "air_compressor": MachineProfile("air_compressor", 2200, 72.0, 415.0, 20.0, 0.08, 80.0),
    "lathe": MachineProfile("lathe", 1000, 42.0, 415.0, 5.0, 0.04, 70.0),
}

SCENARIOS = [
    "healthy",
    "bearing_wear",
    "misalignment",
    "lubrication_failure",
    "motor_imbalance",
    "overheating",
    "critical_failure",
]


@dataclass(frozen=True)
class ScenarioEffect:
    """Multipliers/offsets applied at fault_intensity == 1.0; values at
    intermediate intensity are linearly interpolated between the healthy
    baseline (all multipliers 1.0, all offsets 0) and these."""

    vibration_x_multiplier: float = 1.0
    vibration_y_multiplier: float = 1.0
    vibration_z_multiplier: float = 1.0
    acoustic_offset_db: float = 0.0
    temperature_offset_c: float = 0.0
    current_multiplier: float = 1.0
    rpm_instability: float = 0.0  # fraction of RPM baseline used as extra jitter stddev


SCENARIO_EFFECTS: dict[str, ScenarioEffect] = {
    "healthy": ScenarioEffect(),
    "bearing_wear": ScenarioEffect(
        vibration_x_multiplier=4.5,
        vibration_y_multiplier=4.0,
        vibration_z_multiplier=1.8,
        acoustic_offset_db=8.0,
        temperature_offset_c=4.0,
    ),
    "misalignment": ScenarioEffect(
        vibration_x_multiplier=5.5,
        vibration_y_multiplier=2.0,
        vibration_z_multiplier=1.3,
        acoustic_offset_db=4.0,
        temperature_offset_c=3.0,
        rpm_instability=0.01,
    ),
    "lubrication_failure": ScenarioEffect(
        vibration_x_multiplier=2.2,
        vibration_y_multiplier=2.2,
        vibration_z_multiplier=1.5,
        acoustic_offset_db=10.0,
        temperature_offset_c=14.0,
        current_multiplier=1.15,
    ),
    "motor_imbalance": ScenarioEffect(
        vibration_x_multiplier=3.5,
        vibration_y_multiplier=3.5,
        vibration_z_multiplier=1.2,
        acoustic_offset_db=3.0,
        current_multiplier=1.1,
        rpm_instability=0.015,
    ),
    "overheating": ScenarioEffect(
        vibration_x_multiplier=1.5,
        vibration_y_multiplier=1.5,
        vibration_z_multiplier=1.2,
        acoustic_offset_db=2.0,
        temperature_offset_c=28.0,
        current_multiplier=1.3,
    ),
    "critical_failure": ScenarioEffect(
        vibration_x_multiplier=8.0,
        vibration_y_multiplier=7.5,
        vibration_z_multiplier=4.0,
        acoustic_offset_db=18.0,
        temperature_offset_c=35.0,
        current_multiplier=1.6,
        rpm_instability=0.05,
    ),
}


def get_machine_profile(machine_type: str) -> MachineProfile:
    if machine_type not in MACHINE_PROFILES:
        raise ValueError(f"Unknown machine type: {machine_type}")
    return MACHINE_PROFILES[machine_type]


def get_scenario_effect(scenario: str) -> ScenarioEffect:
    if scenario not in SCENARIO_EFFECTS:
        raise ValueError(f"Unknown scenario: {scenario}")
    return SCENARIO_EFFECTS[scenario]


def interpolate_effect(effect: ScenarioEffect, intensity: float) -> ScenarioEffect:
    """Blends the healthy baseline (all neutral values) toward `effect` by
    `intensity` in [0, 1] -- this is what makes a fault ramp in gradually
    rather than snapping on instantly."""
    intensity = max(0.0, min(1.0, intensity))
    neutral = ScenarioEffect()
    return ScenarioEffect(
        vibration_x_multiplier=_lerp(neutral.vibration_x_multiplier, effect.vibration_x_multiplier, intensity),
        vibration_y_multiplier=_lerp(neutral.vibration_y_multiplier, effect.vibration_y_multiplier, intensity),
        vibration_z_multiplier=_lerp(neutral.vibration_z_multiplier, effect.vibration_z_multiplier, intensity),
        acoustic_offset_db=_lerp(neutral.acoustic_offset_db, effect.acoustic_offset_db, intensity),
        temperature_offset_c=_lerp(neutral.temperature_offset_c, effect.temperature_offset_c, intensity),
        current_multiplier=_lerp(neutral.current_multiplier, effect.current_multiplier, intensity),
        rpm_instability=_lerp(neutral.rpm_instability, effect.rpm_instability, intensity),
    )


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t
