"""
ArduinoDataSource -- the Hardware Mode implementation of IDataSource.

Deliberately near-passive: real Arduino UNO Q hardware
(firmware/YantraRakshak) publishes MQTT directly from its own Python
brick, completely independent of this PC-side application. This class
exists for architectural symmetry (so MODE=hardware and MODE=simulation
are both a real IDataSource the runtime can point at, not a special case)
and as the natural place to add PC-side hardware bookkeeping later (e.g.
health-checking that real devices are publishing) without touching the
simulator or the backend.
"""

import logging

from core.i_data_source import IDataSource

logger = logging.getLogger("yantra_rakshak.simulation")


class ArduinoDataSource(IDataSource):
    def __init__(self):
        self._running = False

    def start(self) -> None:
        self._running = True
        logger.info(
            "Hardware Mode active: no PC-side data generation started. "
            "Real Arduino UNO Q hardware is expected to publish MQTT "
            "telemetry/alert/status directly to the configured broker."
        )

    def stop(self) -> None:
        self._running = False

    def is_running(self) -> bool:
        return self._running
