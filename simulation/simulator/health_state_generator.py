"""
Health State Generator -- converts the simulator's known fault intensity
into the same health/fault/confidence/anomaly_score contract the real
Arduino firmware's AnomalyDetector + Python brick produce. The anomaly
score scale intentionally matches the real trained model's calibrated
thresholds (see docs/MODEL_TRAINING_REPORT.md: warning=1.777191,
critical=2.914409) so a dashboard consuming both modes sees consistent
numbers regardless of source.
"""

import random
from dataclasses import dataclass

# Matches firmware/YantraRakshak/sketch/src/config/Config.h MlConfig
# thresholds exactly -- see docs/MODEL_TRAINING_REPORT.md.
WARNING_THRESHOLD = 1.777191
CRITICAL_THRESHOLD = 2.914409

# Chosen so intensity=1.0 maps to an anomaly_score comfortably above
# CRITICAL_THRESHOLD, matching how a fully-developed real fault scores
# roughly 17x the normal baseline in the real training results.
_INTENSITY_TO_SCORE_SCALE = 4.0
_HEALTHY_BASELINE_SCORE = 0.15
_HEALTHY_SCORE_NOISE_STD = 0.08

_SCENARIO_LABELS = {
    "healthy": "None",
    "bearing_wear": "Bearing Wear",
    "misalignment": "Misalignment",
    "lubrication_failure": "Lubrication Failure",
    "motor_imbalance": "Motor Imbalance",
    "overheating": "Overheating",
    "critical_failure": "Critical Failure",
}


@dataclass
class HealthState:
    health: str  # "Healthy" / "Warning" / "Critical"
    fault: str
    confidence: float
    anomaly_score: float


class HealthStateGenerator:
    def __init__(self, seed: int | None = None):
        self._random = random.Random(seed)

    def generate(self, scenario: str, intensity: float) -> HealthState:
        base_score = _HEALTHY_BASELINE_SCORE + self._random.gauss(0.0, _HEALTHY_SCORE_NOISE_STD)
        anomaly_score = max(0.0, base_score + intensity * _INTENSITY_TO_SCORE_SCALE)

        if anomaly_score > CRITICAL_THRESHOLD:
            health = "Critical"
            ratio = anomaly_score / CRITICAL_THRESHOLD
            confidence = min(ratio, 1.0)
        elif anomaly_score > WARNING_THRESHOLD:
            health = "Warning"
            span = CRITICAL_THRESHOLD - WARNING_THRESHOLD
            confidence = max(0.0, min(1.0, (anomaly_score - WARNING_THRESHOLD) / span))
        else:
            health = "Healthy"
            ratio = anomaly_score / WARNING_THRESHOLD
            confidence = max(0.0, 1.0 - min(ratio, 1.0))

        fault = _SCENARIO_LABELS.get(scenario, "Unclassified") if health != "Healthy" else "None"

        return HealthState(
            health=health,
            fault=fault,
            confidence=round(confidence, 4),
            anomaly_score=round(anomaly_score, 4),
        )
