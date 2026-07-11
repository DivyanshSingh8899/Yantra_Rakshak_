"""
Fault Generator -- tracks how far a fault has progressed since it was
selected, so scenarios ramp in gradually (like a real developing fault)
rather than snapping instantly from healthy to critical. Manual
"Inject Fault" actions jump to a noticeable starting intensity so the
demo/operator sees an immediate reaction, then continue ramping normally.
"""

import time


class FaultGenerator:
    def __init__(self, ramp_duration_seconds: float = 60.0):
        self._ramp_duration_seconds = ramp_duration_seconds
        self._scenario = "healthy"
        self._started_at = time.monotonic()
        self._injected_floor = 0.0

    def set_scenario(self, scenario: str, injected: bool = False) -> None:
        self._scenario = scenario
        self._started_at = time.monotonic()
        self._injected_floor = 0.4 if (injected and scenario != "healthy") else 0.0

    @property
    def scenario(self) -> str:
        return self._scenario

    def get_intensity(self, speed_multiplier: float = 1.0) -> float:
        if self._scenario == "healthy":
            return 0.0
        elapsed = (time.monotonic() - self._started_at) * speed_multiplier
        ramped = min(1.0, elapsed / self._ramp_duration_seconds)
        return max(self._injected_floor, ramped)
