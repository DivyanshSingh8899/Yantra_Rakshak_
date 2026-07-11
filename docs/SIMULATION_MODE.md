# Software Simulation Mode

Extends YantraRakshak with a second execution mode that requires zero code changes to switch to/from — verified end-to-end in this session, not just designed. Nothing under `firmware/`, `machine-learning/`, or the docs describing them was touched.

## The Switch

`config.yaml` (repo root):
```yaml
mode: simulation   # or: hardware
```
This is the only value that determines behavior. `simulation/main.py`'s `_build_data_source()` factory is the only piece of code in the project that reads it:

```
IDataSource (simulation/core/i_data_source.py)
  ├── ArduinoDataSource            -- Hardware Mode: passive; real UNO Q publishes MQTT directly
  └── MachineSimulatorDataSource   -- Simulation Mode: owns the simulator + MQTT publisher
```

## Why the Backend Needed Zero Mode-Awareness

The simulator publishes the **exact** JSON schema the real firmware's `AlertManager`/Python brick produce, to the **exact** same topics:
```
{"machine_id": "...", "timestamp": "...", "health": "...", "fault": "...", "confidence": 0.0, "anomaly_score": 0.0}
plant/{machine_id}/telemetry | alert | status
```
`backend/app/mqtt/subscriber.py` has no `if mode == ...` anywhere in it. The only backend addition mode-adjacent at all is `GET /api/v1/system/mode`, which just reports `config.yaml`'s value for the frontend header badge — it doesn't change how ingestion works.

## New Modules (nothing else was modified)

| Module | Purpose |
|---|---|
| `simulation/core/` | `IDataSource` + its two implementations |
| `simulation/simulator/` | `scenario_engine` (4 machine profiles x 7 scenarios), `virtual_sensors` (RPM/temp/voltage/current/vibration XYZ/acoustic), `fault_generator` (gradual ramp + instant "inject" floor), `sensor_noise_generator`, `health_state_generator` (maps fault intensity onto the *same* calibrated thresholds as the real trained model), `machine_simulator`, `simulation_controller` (start/pause/resume/speed/inject-fault) |
| `simulation/publisher/data_publisher.py` | Builds/publishes the schema above |
| `simulation/main.py` | The `IDataSource` factory + a small FastAPI control API (port 8001) for the frontend panel |
| `backend/`, `frontend/` | Built fresh this session (they didn't exist as code before — only as design docs) so there was something real for Simulation Mode to plug into |

## Verified End-to-End (this session, real processes, not claimed)

1. Started a real MQTT broker, the real FastAPI backend (port 8000), the real simulation control API (port 8001, auto-started `Lathe-01` on `mode: simulation`), and the real Vite frontend (port 5173).
2. Confirmed `GET /api/v1/system/mode` → `{"mode": "simulation"}`.
3. Confirmed the simulator's MQTT messages made the backend auto-register `Lathe-01` and show it `online`/`healthy` — with **no manual registration**.
4. Called `POST /simulation/inject-fault {"scenario": "critical_failure"}` — watched real alerts appear in the backend (`GET /api/v1/alerts/active`), correctly escalating from `warning` to `critical` as the fault intensity ramped, exactly matching the gradual-ramp design.
5. Confirmed the LLM Manager fired for each alert and degraded gracefully (Ollama not running in this environment → `generation_status: "failed"` with the deterministic fallback text, not a crash).
6. Confirmed WebSocket broadcasts arrive in real time (`alert:new`, `recommendation:ready`).
7. Screenshotted the live dashboard (Playwright): machine grid, live alert feed showing the real Warning→Critical escalation, and the Simulation Control Panel (Start/Pause/Resume, machine/scenario selectors, speed slider, inject-fault buttons) all rendering and functioning against the real backend.

## Running It Yourself

```
# Terminal 1 — MQTT broker (any broker works; Mosquitto if installed)
mosquitto -v

# Terminal 2 — backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --port 8000

# Terminal 3 — simulation (reads config.yaml's mode automatically)
cd simulation && pip install -r requirements.txt && python main.py

# Terminal 4 — frontend
cd frontend && npm install && npm run dev
```
Open `http://localhost:5173`. To switch to Hardware Mode: set `mode: hardware` in `config.yaml`, restart `simulation/main.py` (it becomes passive), and connect real Arduino UNO Q hardware per `docs/INSTALLATION_GUIDE.md` — the backend and frontend need no changes or restarts to accept either.

## Known Gap (honest, not a hidden bug)

Machine cards show "unknown type" for simulator-created machines because the real MQTT JSON schema (matched exactly, per the requirement) doesn't carry `machine_type` — neither hardware mode nor simulation mode sends it over MQTT. Register a machine's type in advance via `POST /api/v1/machines` if you want it populated; this is consistent behavior across both modes, not a simulation-specific shortcut.
