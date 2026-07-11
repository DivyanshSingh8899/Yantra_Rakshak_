"""
Simulation Controller -- the runtime loop that ticks a MachineSimulator on
a schedule and hands each tick to the DataPublisher. Owns start/pause/
resume/speed/inject-fault/select-machine, all of which simulation/main.py's
control API exposes over HTTP for the frontend's Simulation Control Panel.
"""

import threading

from simulator.machine_simulator import MachineSimulator


class SimulationController:
    def __init__(self, data_publisher, tick_interval_seconds: float = 0.256):
        # 0.256s matches the real firmware's ~128-sample-at-500Hz window
        # cadence (see docs/FIRMWARE_ARCHITECTURE.md) so both modes report
        # at a comparable rate.
        self._publisher = data_publisher
        self._tick_interval_seconds = tick_interval_seconds
        self._simulator: MachineSimulator | None = None
        self._speed_multiplier = 1.0
        self._running = False
        self._paused = False
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self, machine_id: str, machine_type: str, scenario: str = "healthy") -> None:
        if self._running:
            self.stop()

        self._simulator = MachineSimulator(machine_id, machine_type, scenario)
        self._running = True
        self._paused = False
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._publisher.publish_status(machine_id, "online")

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def stop(self) -> None:
        was_running = self._running
        machine_id = self._simulator.machine_id if self._simulator else None
        self._running = False
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        if was_running and machine_id:
            self._publisher.publish_status(machine_id, "offline")

    def set_speed(self, speed_multiplier: float) -> None:
        self._speed_multiplier = max(0.1, speed_multiplier)

    def set_scenario(self, scenario: str) -> None:
        if self._simulator is not None:
            self._simulator.set_scenario(scenario)

    def inject_fault(self, scenario: str) -> None:
        if self._simulator is not None:
            self._simulator.set_scenario(scenario, injected=True)

    def get_state(self) -> dict:
        return {
            "running": self._running,
            "paused": self._paused,
            "machine_id": self._simulator.machine_id if self._simulator else None,
            "machine_type": self._simulator.machine_type if self._simulator else None,
            "scenario": self._simulator.scenario if self._simulator else None,
            "speed": self._speed_multiplier,
        }

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            if not self._paused and self._simulator is not None:
                tick = self._simulator.tick(self._speed_multiplier)
                self._publisher.publish_tick(tick)

            effective_interval = self._tick_interval_seconds / self._speed_multiplier
            self._stop_event.wait(timeout=effective_interval)
