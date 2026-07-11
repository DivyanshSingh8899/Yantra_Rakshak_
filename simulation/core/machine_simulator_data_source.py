"""
MachineSimulatorDataSource -- the Simulation Mode implementation of
IDataSource. Owns the DataPublisher (MQTT) and SimulationController
(the tick loop), and is the thing simulation/main.py's control API
(start/pause/resume/speed/inject-fault) actually drives.
"""

import logging

from core.i_data_source import IDataSource
from publisher.data_publisher import DataPublisher
from simulator.simulation_controller import SimulationController

logger = logging.getLogger("yantra_rakshak.simulation")


class MachineSimulatorDataSource(IDataSource):
    def __init__(self, broker_host: str, broker_port: int):
        self._publisher = DataPublisher(broker_host, broker_port)
        self.controller = SimulationController(self._publisher)
        self._running = False

    def start(self) -> None:
        self._publisher.connect()
        self._running = True
        logger.info("Simulation Mode active: MachineSimulatorDataSource connected to MQTT broker.")

    def stop(self) -> None:
        self.controller.stop()
        self._publisher.disconnect()
        self._running = False

    def is_running(self) -> bool:
        return self._running
