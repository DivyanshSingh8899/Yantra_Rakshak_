"""
Simulation module entry point.

This is the ONE place that reads config.yaml's `mode` and picks between
ArduinoDataSource and MachineSimulatorDataSource via the IDataSource
interface -- changing `mode` in config.yaml and restarting this process is
the entire "switch modes" operation; no other file changes.

Also hosts a small FastAPI control API (default port 8001) for the
frontend's Simulation Control Panel -- kept separate from the main backend
(backend/app/main.py, port 8000) since these are simulator control
commands, not machine telemetry, and the backend must stay untouched.
"""

import logging

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import config
from core.arduino_data_source import ArduinoDataSource
from core.machine_simulator_data_source import MachineSimulatorDataSource
from simulator.scenario_engine import MACHINE_PROFILES, SCENARIOS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("yantra_rakshak.simulation")

app = FastAPI(title="YantraRakshak Simulation Control API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Lets a public HTTPS origin (e.g. the Vercel-deployed frontend) call this
    # localhost-bound API -- Chrome's Private Network Access checks block
    # that preflight otherwise ("Disallowed CORS private-network").
    allow_private_network=True,
)


def _build_data_source():
    """The IDataSource factory: the only piece of code in the whole
    project that inspects config.yaml's mode value to decide behavior."""
    mode = config.get_mode()
    broker_host, broker_port = config.get_mqtt_settings()

    if mode == "simulation":
        return MachineSimulatorDataSource(broker_host, broker_port)
    return ArduinoDataSource()


data_source = _build_data_source()


class StartRequest(BaseModel):
    machine_id: str
    machine_type: str
    scenario: str = "healthy"


class ScenarioRequest(BaseModel):
    scenario: str


class SpeedRequest(BaseModel):
    speed: float


def _require_simulation_mode() -> MachineSimulatorDataSource:
    if not isinstance(data_source, MachineSimulatorDataSource):
        raise HTTPException(
            status_code=409,
            detail="Simulation controls are unavailable in Hardware Mode (config.yaml mode=hardware).",
        )
    return data_source


@app.on_event("startup")
def on_startup():
    data_source.start()

    if isinstance(data_source, MachineSimulatorDataSource):
        default_machines = config.get_default_machines()
        if default_machines:
            first_machine = default_machines[0]
            data_source.controller.set_speed(config.get_default_speed())
            data_source.controller.start(
                machine_id=first_machine["machine_id"],
                machine_type=first_machine["machine_type"],
                scenario=config.get_default_scenario(),
            )
            logger.info("Auto-started simulation for %s on startup.", first_machine["machine_id"])


@app.on_event("shutdown")
def on_shutdown():
    data_source.stop()


@app.get("/simulation/state")
def get_state():
    if isinstance(data_source, MachineSimulatorDataSource):
        return {"mode": "simulation", **data_source.controller.get_state()}
    return {"mode": "hardware", "running": data_source.is_running()}


@app.get("/simulation/machines")
def list_machine_types():
    return {"machine_types": list(MACHINE_PROFILES.keys()), "configured_machines": config.get_default_machines()}


@app.get("/simulation/scenarios")
def list_scenarios():
    return {"scenarios": SCENARIOS}


@app.post("/simulation/start")
def start_simulation(request: StartRequest):
    ds = _require_simulation_mode()
    ds.controller.start(request.machine_id, request.machine_type, request.scenario)
    return ds.controller.get_state()


@app.post("/simulation/pause")
def pause_simulation():
    ds = _require_simulation_mode()
    ds.controller.pause()
    return ds.controller.get_state()


@app.post("/simulation/resume")
def resume_simulation():
    ds = _require_simulation_mode()
    ds.controller.resume()
    return ds.controller.get_state()


@app.post("/simulation/scenario")
def set_scenario(request: ScenarioRequest):
    ds = _require_simulation_mode()
    ds.controller.set_scenario(request.scenario)
    return ds.controller.get_state()


@app.post("/simulation/speed")
def set_speed(request: SpeedRequest):
    ds = _require_simulation_mode()
    ds.controller.set_speed(request.speed)
    return ds.controller.get_state()


@app.post("/simulation/inject-fault")
def inject_fault(request: ScenarioRequest):
    ds = _require_simulation_mode()
    ds.controller.inject_fault(request.scenario)
    return ds.controller.get_state()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
