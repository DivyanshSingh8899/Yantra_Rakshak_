"""
IDataSource -- the interface that makes MODE=hardware / MODE=simulation a
single, no-code-change switch. simulation/main.py's factory picks between
ArduinoDataSource and MachineSimulatorDataSource based solely on
config.yaml's `mode` value; nothing else in the system needs to know which
one is active.
"""

from abc import ABC, abstractmethod


class IDataSource(ABC):
    @abstractmethod
    def start(self) -> None:
        """Begins producing data (or, for hardware mode, begins whatever
        passive monitoring is appropriate)."""
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        """Stops producing data / releases resources."""
        raise NotImplementedError

    @abstractmethod
    def is_running(self) -> bool:
        raise NotImplementedError
