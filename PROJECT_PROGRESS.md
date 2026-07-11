# Yantra Rakshak – Project Progress

> **This file is the single source of truth for project continuity.** Read it before starting any new task. Update it (append, never overwrite) immediately after every change — before moving to the next file or task.

---

## 1. Project Overview

**Current objective**: An offline predictive-maintenance system for MSME machines. Vibration (and originally acoustic) anomaly detection via TinyML, alerts published over MQTT, ingested by a FastAPI/SQLite backend, visualized in a React dashboard, with a local LLM (Ollama) generating maintenance recommendations. The system supports **two execution modes** behind one config switch: real Arduino UNO Q hardware, or a full software simulator — the backend/frontend/database/LLM cannot tell which one is active.

**Overall architecture**:
```
Hardware Mode:  Arduino UNO Q (MPU6050) --Bridge RPC--> Python brick (Qualcomm Linux) --MQTT--> Backend --WS--> Frontend
Simulation Mode: simulation/ (virtual sensors + fault engine)                          --MQTT--> Backend --WS--> Frontend
```
Both modes publish the **identical JSON schema** to the **identical MQTT topics**; the backend's MQTT subscriber has no mode-awareness at all.

**Hardware Mode status**: Firmware code-complete and **really compiled successfully** against the real `arduino:zephyr` core (110,684 bytes flash / 60,816 bytes RAM — see `docs/COMPILE_VERIFICATION.md`). TinyML model trained on real CWRU Bearing Data Center recordings (not synthetic). Not yet flashed/run on physical hardware (none available in this environment) — expected to arrive and be tested next.

**Simulation Mode status**: Fully implemented and **verified running end-to-end** in this environment: real MQTT broker, real FastAPI backend, real simulation control API, real React dashboard, all screenshotted mid-run showing a live fault-injection scenario correctly escalating Warning → Critical.

---

## 2. Completed Modules

### Firmware — MCU sketch (`firmware/YantraRakshak/sketch/`)
- **Files**: `sketch.ino`, `sketch.yaml`, `src/config/Config.h`, `src/utils/Logger.{h,cpp}`, `src/buffer/CircularBuffer.h`, `src/sensors/MPU6050Sensor.{h,cpp}`, `src/sensors/SensorManager.{h,cpp}`, `src/signal/SignalProcessor.{h,cpp}`, `src/bridge/BridgeRelay.{h,cpp}`, `src/led/LEDController.{h,cpp}`
- **Features**: MPU6050 vibration sampling (500 Hz, at-rest zero-offset calibration), 128-sample windowed circular buffer, 5-feature extraction (mean/rms/peak/crestFactor/kurtosis of 3-axis acceleration magnitude) with real trained standardization constants baked in, `Arduino_RouterBridge` RPC relay to the Python brick, RGB LED status (Green/Yellow/Red/Blink-Red)
- **Dependencies**: Adafruit MPU6050 + Unified Sensor + BusIO, `Arduino_RouterBridge` (+ its `Arduino_RPClite`/MsgPack chain)
- **Status**: **Completed**, real compile verified (`arduino-cli compile --fqbn arduino:zephyr:unoq` succeeded)

### Firmware — Python brick (`firmware/YantraRakshak/python/`)
- **Files**: `main.py`, `config.py`, `requirements.txt`, `model/autoencoder_int8.tflite`, `test_offline_verification.py`
- **Features**: Receives feature vectors via Bridge, runs the real trained TFLite model, classifies Healthy/Warning/Critical, builds the exact JSON alert/heartbeat schema, publishes MQTT (paho-mqtt), returns status to MCU for LED, periodic heartbeat
- **Dependencies**: `tflite-runtime`/`tensorflow`, `numpy`, `paho-mqtt`, `arduino.app_utils` (board-provided, not pip-installable)
- **Status**: **Completed**, offline-verified against real feature vectors (`docs/PYTHON_VERIFICATION.md`)

### Experimental on-MCU inference (`firmware/YantraRakshak/experimental-mcu-inference/`)
- **Files**: `ml/AnomalyDetector.{h,cpp}`, `ml/model_data.{h,cpp}`
- **Features**: Same real trained model as a C array (`g_model[]`/`g_model_len`) + TFLM wrapper, for teams who want to attempt on-MCU inference
- **Status**: **Not part of default build** — real compile attempt proved TensorFlow Lite Micro isn't available through `arduino:zephyr`'s library resolution; kept outside `sketch/src/` deliberately

### TinyML training pipeline (`machine-learning/`)
- **Files**: `training/train_autoencoder.py`, `models/exported/autoencoder_int8.tflite`, `models/exported/calibration.json`, `requirements.txt`
- **Features**: Downloads/loads real CWRU `.mat` files, decimates 12kHz→500Hz, extracts 5 features, trains a 5-4-2-4-5 dense autoencoder, quantizes to INT8, verifies quantized model preserves float-model error separation
- **Dependencies**: `tensorflow`, `numpy`, `scipy`
- **Status**: **Completed**. Real result: 100% fault detection, 7.2% false-positive rate on held-out fault data (see `docs/MODEL_TRAINING_REPORT.md`)

### Backend (`backend/`)
- **Files**: see §4 and §11
- **Status**: **Completed** (minimal-but-real scope), running and verified live

### Frontend (`frontend/`)
- **Files**: see §5 and §11
- **Status**: **Completed** (minimal-but-real scope), running and verified live

### Simulation (`simulation/`)
- **Files**: see §6 and §11
- **Status**: **Completed**, running and verified live

---

## 3. Recent Changes

### 2026-07-11 — Architecture & design phase
- **Files modified**: none (chat-only design output; no files existed yet)
- **Summary**: Produced architecture, folder structure, dev environment plan, hardware architecture, firmware architecture + class diagrams, TinyML pipeline math design, backend architecture (API docs/DB schema/ER diagram), React dashboard design, LLM assistant design, and a master implementation roadmap.
- **Reason**: Initial project planning requested by user, explicitly "no code yet."

### 2026-07-11 — Firmware implementation (first pass)
- **Files modified**: created `firmware/YantraRakshak/` full tree (Config, Logger, TimeSync, CircularBuffer, MPU6050Sensor, INMP441Sensor, SensorManager, SignalProcessor, AnomalyDetector, model_data stubs, AlertManager, WiFiManager, MQTTManager, LEDController, main .ino, docs)
- **Summary**: Generated the complete monolithic single-core Arduino sketch per user's file-by-file request.
- **Reason**: User requested full firmware generation, one file at a time.

### 2026-07-11 — Blocker resolution: real ML pipeline + real Arduino API verification
- **Files modified**: Deleted `INMP441Sensor.*`, `WiFiManager.*`, `MQTTManager.*`, `TimeSync.*`, `alerts/AlertManager.*` from the MCU sketch; restructured `firmware/YantraRakshak/` into `app.yaml` + `sketch/` + `python/`; added `simulation`-unrelated `bridge/BridgeRelay.*`; rewrote `Config.h`, `SignalProcessor.*`, `AnomalyDetector.*`; added `python/main.py`, `config.py`, `requirements.txt`, `model/`; added `machine-learning/training/train_autoencoder.py`; added 6 new `docs/*.md` (API verification, model training report, compile verification, python verification, validation report) plus updates to wiring/installation/build/library/memory docs.
- **Summary**: Real web research proved several original assumptions wrong (Wi-Fi/MQTT belongs to the Linux MPU side, not the MCU; I2S mic pins not exposed on UNO Q; TFLM not available via `arduino:zephyr`'s library resolution; PlatformIO unsupported). Downloaded real CWRU Bearing Data Center data, trained a real autoencoder, quantized it, generated real `model_data.cpp`/`.h`. Installed real `arduino-cli` + `arduino:zephyr` core and got a real successful compile.
- **Reason**: User explicitly required resolving two "integration blockers" with real work, not assumptions — "do not stop after explaining, actually generate every missing file."

### 2026-07-11 — Software Simulation Mode + first real backend/frontend
- **Files modified**: created `config.yaml`; created all of `backend/` (models, database, config, services, mqtt subscriber, websocket manager, API routes, main.py, requirements, .env.example); created all of `frontend/` (Vite/React/Tailwind scaffold, StatTile/StatusBadge/MachineCard/AlertFeedItem, Dashboard page, SimulationControlPanel, api/websocket services, App.jsx); created all of `simulation/` (IDataSource + ArduinoDataSource + MachineSimulatorDataSource, scenario_engine, sensor_noise_generator, fault_generator, virtual_sensors, health_state_generator, machine_simulator, simulation_controller, data_publisher, config.py, main.py, requirements.txt); added `docs/SIMULATION_MODE.md`; updated `.gitignore`.
- **Summary**: Discovered backend/frontend didn't exist as code (only earlier design docs) — user chose to implement a minimal real backend+frontend first, then the full simulation module. Ran everything live (MQTT broker via `amqtt`, backend on :8000, simulation control API on :8001, frontend on :5173), injected a real fault scenario, and screenshotted the live dashboard showing correct Warning→Critical escalation.
- **Reason**: User requested a Software Simulation Mode extension without touching firmware/TinyML/MQTT topic schema/DB schema/etc., behind a single `MODE` config switch, and explicitly asked for a "final working website."

### 2026-07-11 — Project continuity file established
- **Files modified**: created `PROJECT_PROGRESS.md` (this file); updated `.gitignore` (log files, DB file, venvs, node_modules, screenshot scratch files).
- **Summary**: Established the living project log per user's standing instruction.
- **Reason**: User instructed that all future work must keep this file up to date, appended to, and read before starting new tasks.

### 2026-07-11 — Frontend UI/UX overhaul: charts, fleet heatmap, dark mode, Hardware Setup page
- **Files modified**: added `recharts` dependency; `tailwind.config.js` (`darkMode: "media"` → `"class"`); added `src/hooks/useDarkMode.js`, `src/components/common/ThemeToggle.jsx`, `src/components/charts/{TrendLineChart,Sparkline,HealthMeter,FleetHeatmap}.jsx`, `src/components/machines/MachineDetailModal.jsx`, `src/data/wiringData.js`, `src/pages/HardwareSetup.jsx`; rewrote `src/App.jsx` (tab nav + theme toggle), `src/pages/Dashboard.jsx` (fleet heatmap + click-through modal), `src/components/alerts/MachineCard.jsx` (clickable, hover states, embedded sparkline), `src/components/common/StatTile.jsx` (accent colors); added `@keyframes fadeIn` to `src/index.css`; added root `.claude/launch.json` dev-server config (project root is outside the primary working directory, so the config lives at `D:\Internship\Portfolio\.claude\launch.json` instead).
- **Summary**: Implemented the three previously-pending chart components (`TrendLineChart`, `HealthMeter`, `FleetHeatmap`) plus a `Sparkline` for machine cards, all reading real data from the existing `/machines/{id}/telemetry` endpoint — no backend changes needed. Added a manual dark/light theme toggle (persisted in `localStorage`, defaults to system preference) and a tabbed nav (`Dashboard` / `Hardware Setup`). Built a new interactive `HardwareSetup` page: a hand-laid-out SVG wiring diagram (UNO Q ↔ MPU6050 ↔ RGB LED) driven by `src/data/wiringData.js` (sourced from `docs/WIRING_DIAGRAM.md`), with hoverable/clickable wires that highlight and show connection details, plus a synced accessible table fallback. MachineCard/FleetHeatmap clicks open a `MachineDetailModal` with a live-polling trend chart + health gauge.
- **Verified live**: reused the already-running backend/simulation from an earlier session (still serving real `Lathe-01`/`Motor-01`/`Motor-02` data) — its MQTT broker had gone stale, so a fresh `amqtt` broker was started, which caused the existing backend and simulation processes to auto-reconnect and resume publishing in real time. Restarted the Vite dev server (a stale pre-existing instance hadn't picked up the `darkMode: "class"` Tailwind config change). Confirmed via the Browser pane: dashboard renders KPI tiles, fleet heatmap, machine cards with sparklines, and a live alert feed against real data; clicking a heatmap cell/card opens the detail modal with a working `HealthMeter` gauge; theme toggle correctly flips `dark` class + `localStorage` and repaints; Hardware Setup page renders the wiring diagram correctly in both themes, wire click/hover correctly surfaces connection details and highlights the matching pin-reference table row. No console errors.
- **Reason**: User requested improved, more interactive UI/UX, "reliable graphs," and a way to see the complete Arduino hardware setup in the dashboard — this was scoped down via clarifying questions to: (1) per-machine trend + fleet health overview charts, and (2) an interactive wiring-diagram page, both confirmed by the user as the recommended options.
- **Pending from this work**: `Sparkline` fetches telemetry per-card on mount without a shared cache or polling refresh — fine at current fleet sizes (single digits) but would need batching/caching if the fleet grows large. Machine Details/Alert History/Recommendations/Analytics/Settings pages from the original design are still not implemented (only the inline `MachineDetailModal` exists so far).

### 2026-07-11 — Pushed to GitHub (github.com/DivyanshSingh8899/Yantra_Rakshak_)
- **Files modified**: `.gitignore` (added `.venv/`, `node_modules/`, `*.log`, `database/*.db`); `README.md` (rewritten — the pre-existing one was a corrupted UTF-16 placeholder); deleted stray root `node_modules/` and four dev-session `.log` files (not deliverables); no other files changed (first real commit of everything already documented above).
- **Summary**: User provided the GitHub URL `https://github.com/DivyanshSingh8899/Yantra_Rakshak_.git`. Discovered the local repo's existing `origin` remote pointed at a *misspelled* repo (`Yantra_Raskhak_`) with only one prior commit (a garbled README, no real project files). Per user's choice, updated `origin` to the correctly-spelled URL, cleaned up non-deliverable artifacts, committed the entire project (firmware, ML pipeline + trained model files, backend, frontend, simulation module, all docs, `PROJECT_PROGRESS.md`, `config.yaml`), fetched first to confirm no conflicting history on the remote, then pushed `main` — a clean fast-forward, not a forced overwrite.
- **Reason**: User wants the project's canonical home on GitHub at the correct repo name; explicit confirmation was sought (and given) before changing the remote and pushing, since both are shared/visible actions.

---

## 4. Backend Progress

**Stack**: FastAPI + SQLAlchemy + SQLite, paho-mqtt, WebSockets, httpx (Ollama calls), PyYAML (`config.yaml`).

**Completed REST APIs** (`backend/app/api/`):
| Method | Path | File |
|---|---|---|
| GET | `/api/v1/machines` | `machines.py` |
| POST | `/api/v1/machines` | `machines.py` |
| GET | `/api/v1/machines/{machine_id}` | `machines.py` |
| GET | `/api/v1/machines/{machine_id}/telemetry` | `machines.py` |
| GET | `/api/v1/machines/{machine_id}/health` | `machines.py` |
| GET | `/api/v1/alerts` | `alerts.py` |
| GET | `/api/v1/alerts/active` | `alerts.py` |
| GET | `/api/v1/alerts/{alert_id}` | `alerts.py` |
| POST | `/api/v1/alerts/{alert_id}/acknowledge` | `alerts.py` |
| POST | `/api/v1/alerts/{alert_id}/resolve` | `alerts.py` |
| GET | `/api/v1/recommendations/{alert_id}` | `recommendations.py` |
| POST | `/api/v1/recommendations/{alert_id}/regenerate` | `recommendations.py` |
| GET | `/api/v1/system/mode` | `system.py` |
| GET | `/api/v1/system/health` | `system.py` |
| WS | `/ws` | `main.py` |

**Database**: SQLite (`database/yantrarakshak.db`), SQLAlchemy models in `backend/app/db/models.py` — `Machine`, `Telemetry`, `Alert`, `Recommendation` (matches the originally-designed ER diagram). `init_db()` creates tables idempotently on startup.

**MQTT integration**: `backend/app/mqtt/subscriber.py` — subscribes to `plant/+/telemetry`, `plant/+/alert`, `plant/+/status`; parses the exact schema `{"machine_id","timestamp","health","fault","confidence","anomaly_score"}`; auto-registers unseen machines; **has no mode-awareness whatsoever** (this is intentional and load-bearing for the "backend can't tell modes apart" requirement).

**WebSocket support**: `backend/app/websocket/manager.py` — broadcasts `telemetry:update`, `alert:new`, `machine:status`, `recommendation:ready` events; bridges the sync MQTT thread to the async FastAPI event loop via `run_coroutine_threadsafe`.

**AI integration**: `backend/app/services/llm_manager.py` — real HTTP call to Ollama (`/api/generate`), deterministic fallback text + `generation_status: "failed"` if unreachable (verified: Ollama is not running in this dev environment, and the fallback path was exercised live).

**Status**: Completed (minimal-but-real scope — no auth, no pagination, no machine_thresholds table yet). Verified running.

---

## 5. Frontend Progress

**Stack**: React 18 + Vite + Tailwind CSS.

**Completed pages**: `Dashboard.jsx` — KPI row (Total Machines/Online/Active Alerts/Fleet Health), fleet heatmap, machine grid (click-through to detail modal), live alert feed (WebSocket-driven). `HardwareSetup.jsx` — interactive SVG wiring diagram (UNO Q ↔ MPU6050 ↔ RGB LED) with hover/click connection details and a synced pin-reference table.

**Completed components**:
- `components/common/StatTile.jsx` (accent colors), `StatusBadge.jsx`, `ThemeToggle.jsx`
- `components/alerts/MachineCard.jsx` (clickable, hover states, embedded sparkline), `AlertFeedItem.jsx`
- `components/charts/TrendLineChart.jsx`, `Sparkline.jsx`, `HealthMeter.jsx`, `FleetHeatmap.jsx`
- `components/machines/MachineDetailModal.jsx` — gauge + trend chart + status detail, opened from a machine card or heatmap cell
- `components/simulation/SimulationControlPanel.jsx` — Start/Pause/Resume, machine ID/type selectors, scenario selector, speed slider, inject-fault buttons (talks directly to the simulation control API on :8001, not the main backend)

**Services**: `services/api.js` (REST client), `services/websocket.js` (auto-reconnecting WS client)

**Charts/animations**: `recharts`-based `TrendLineChart` (per-machine anomaly-score history with warning/critical reference lines) and `Sparkline` (compact card-embedded trend), both against `/machines/{id}/telemetry`; hand-built SVG `HealthMeter` gauge; `FleetHeatmap` status grid. Manual dark/light theme toggle (`useDarkMode` hook, `localStorage`-persisted, system-preference default).

**Pending work**: Machine Details, Alert History, Recommendations, Analytics, Settings pages (designed earlier in chat, not yet implemented as code — `MachineDetailModal` covers a subset of "Machine Details" inline); table-view accessibility twin for the alert feed; `Sparkline`'s per-card telemetry fetch has no shared cache — revisit if the fleet grows large.

**Status**: Completed (minimal scope + chart/theming/hardware-setup pass). Verified running and rendering correctly via live Browser-pane testing during this session (including interactive gauge, heatmap, modal, theme toggle, and wiring-diagram hover/click).

---

## 6. Simulation Progress

**Modules** (`simulation/`):
- `core/i_data_source.py` — `IDataSource` ABC (`start`/`stop`/`is_running`)
- `core/arduino_data_source.py` — Hardware Mode implementation (passive/logging only)
- `core/machine_simulator_data_source.py` — Simulation Mode implementation (owns publisher + controller)
- `simulator/scenario_engine.py` — 4 `MachineProfile`s (electric_motor, water_pump, air_compressor, lathe) × 7 `ScenarioEffect`s, with linear intensity interpolation
- `simulator/sensor_noise_generator.py` — per-sensor Gaussian noise (RPM, temp, voltage, current, vibration, acoustic)
- `simulator/fault_generator.py` — gradual fault-intensity ramp (default 60s to full), instant-inject floor (0.4) for responsive demos
- `simulator/virtual_sensors.py` — produces `VirtualSensorReading` (rpm, temperature_c, voltage_v, current_a, vibration_x/y/z_g, acoustic_db)
- `simulator/health_state_generator.py` — maps fault intensity to `{health, fault, confidence, anomaly_score}` using the **same real calibrated thresholds** as the trained model (warning=1.777191, critical=2.914409)
- `simulator/machine_simulator.py` — orchestrates one machine's tick
- `simulator/simulation_controller.py` — the run loop (256ms base tick, matching real firmware window cadence) + start/pause/resume/speed/scenario/inject-fault
- `publisher/data_publisher.py` — builds/publishes the exact firmware JSON schema, with the same immediate-alert/30s-heartbeat gating as the real Python brick
- `config.py` — reads root `config.yaml`
- `main.py` — the `IDataSource` factory (reads `mode`) + FastAPI control API on port 8001

**Supported machine types**: electric_motor, water_pump, air_compressor, lathe.

**Supported scenarios/health states**: healthy, bearing_wear, misalignment, lubrication_failure, motor_imbalance, overheating, critical_failure.

**Status**: Completed, verified running (auto-started `Lathe-01` on boot per `config.yaml`'s configured default machines; fault injection tested live end-to-end).

---

## 7. Hardware Progress

**Board**: Arduino UNO Q — STM32U585 (Cortex-M33) running Arduino sketches over Zephyr OS, paired with a Qualcomm QRB2210 running Debian Linux. FQBN: `arduino:zephyr:unoq`.

**Supported sensors**: MPU6050 (I2C, 3-axis accel + gyro; only accel magnitude currently used by the trained model).

**Removed/blocked sensor**: INMP441 (I2S mic) — confirmed via a real UNO Q user forum report that I2S pins are not exposed on this board's headers. Not wired into current firmware or the trained model.

**TinyML integration**: Primary/confirmed-working path is Python-side inference on the Qualcomm Linux MPU (`firmware/YantraRakshak/python/main.py`, using `tflite-runtime`/`tensorflow`). Secondary/experimental path is on-MCU TFLM (`experimental-mcu-inference/`), not part of the default build — real compile attempt proved it's unavailable through `arduino:zephyr`'s library resolution.

**MQTT firmware**: MQTT does **not** run on the MCU. It runs on the Python brick (Qualcomm Linux side) via `paho-mqtt`, receiving feature data from the MCU over `Arduino_RouterBridge` RPC (`Bridge.call`/`Bridge.provide`).

**Hardware assumptions/caveats** (see `docs/ARDUINO_UNO_Q_API_VERIFICATION.md` for full sourcing):
- `Bridge.call()`'s exact timeout behavior on a non-responding Python side is unconfirmed.
- Python-side `Bridge.provide()` is inferred from the router's symmetric design, not directly quoted in an official example.
- `app.yaml`'s exact key schema is a best-effort reconstruction (regenerate via Arduino App Lab to confirm).
- No physical board has been used in this environment — flashing, the live RPC round-trip, and `arduino.app_utils` import are unverified pending real hardware.

**Status**: Firmware code-complete, really compiled. Awaiting physical hardware arrival for flash/run verification.

---

## 8. Known Issues

- **Machine type not populated for MQTT-originated machines**: the real JSON schema (matched exactly in both modes) doesn't carry `machine_type`, so auto-registered machines show "unknown type" on the dashboard until manually registered via `POST /api/v1/machines`. Not a bug — a consequence of matching the real schema exactly.
- **On-MCU TFLM inference unavailable**: confirmed via real compile failure that TensorFlow Lite Micro isn't reachable through `arduino:zephyr`'s Arduino CLI library resolution. Kept as an experimental, non-default path (`experimental-mcu-inference/`).
- **Domain gap in the trained model**: trained on CWRU lab-grade accelerometer data (decimated 12kHz→500Hz to approximate deployment conditions), not on data from the actual deployed MPU6050. Current thresholds are an honest bootstrap calibration, not a final production one — recalibrate once real hardware data is available.
- **No MIMII/audio branch**: MIMII dataset's smallest file is 6.9GB — infeasible to download in this environment. Combined with the I2S hardware blocker, the audio/microphone sensing branch was dropped entirely rather than faked.
- **LLM (Ollama) not running in this dev environment**: `LLMManager` correctly falls back to a deterministic template (`generation_status: "failed"`) — this is graceful degradation, verified live, not a bug, but real recommendation quality is unverified until Ollama is actually running.
- **PlatformIO unsupported**: confirmed via an open GitHub issue against `platformio/platform-ststm32` — Arduino CLI is the only supported build path for this board.
- **FastAPI `@app.on_event` deprecation warnings**: both `backend/app/main.py` and `simulation/main.py` use the deprecated `on_event` startup/shutdown hooks (functional, but FastAPI recommends `lifespan` handlers going forward). Not yet migrated.
- **No physical hardware tested**: everything under "Hardware Progress" beyond compilation is unverified pending the board's arrival.
- ~~**Runtime dev artifacts present in the working tree**~~ — **RESOLVED 2026-07-11**: `backend.log`, `frontend.log`, `mqtt_broker.log`, `simulation.log`, and a stray root-level `node_modules/` (from a one-off Playwright screenshot check) were deleted; `.gitignore` extended to cover `.venv/`, `node_modules/`, `*.log`, and `database/*.db` going forward.
- **Repo's original README.md was corrupted**: the pre-existing repo had a UTF-16-encoded, garbled `README.md` (`# Yantra_Raskhak_` with mangled bytes, from the original misspelled-repo scaffold). Replaced with a proper UTF-8 README pointing to `PROJECT_PROGRESS.md` and `docs/`.

---

## 9. Next Development Tasks

- [x] Architecture, folder structure, dev environment, hardware/firmware/TinyML design docs
- [x] Backend architecture, dashboard design, LLM design (docs only, then later as real code)
- [x] Master implementation roadmap
- [x] Full MCU sketch generated (first pass, later corrected)
- [x] Real Arduino UNO Q API verification against official sources
- [x] Real CWRU dataset download + real autoencoder training + INT8 quantization
- [x] Real `model_data.cpp`/`.h` generation from the trained model
- [x] Real successful `arduino-cli` compile against `arduino:zephyr`
- [x] FastAPI project created (minimal, real)
- [x] SQLite schema completed (Machine/Telemetry/Alert/Recommendation)
- [x] MQTT integration (mode-agnostic subscriber)
- [x] WebSocket support
- [x] Ollama integration (with graceful fallback)
- [x] React Dashboard (minimal: KPI row, machine grid, live alert feed)
- [x] Simulation module (IDataSource, 4 machine profiles × 7 scenarios, fault ramping, MQTT publisher)
- [x] Simulation Control Panel (frontend)
- [x] End-to-end live verification (broker + backend + simulation + frontend, screenshotted)
- [x] `PROJECT_PROGRESS.md` established
- [x] Chart components (TrendLineChart, HealthMeter, FleetHeatmap) per original dashboard design
- [x] Dark mode toggle (accessibility table-view twin for alert feed still pending)
- [x] Interactive Arduino UNO Q hardware-setup/wiring-diagram page
- [ ] Migrate `@app.on_event` to FastAPI `lifespan` handlers (backend + simulation)
- [ ] Alert History, Recommendations, Analytics, Settings pages (frontend) — Machine Details partially covered by `MachineDetailModal`
- [ ] `machine_thresholds` table + per-machine configurable warning/critical thresholds via API
- [ ] Accessibility table-view twin for the live alert feed
- [ ] Flash real Arduino UNO Q hardware once available; verify live `Arduino_RouterBridge` round-trip
- [ ] Recalibrate ML thresholds against real MPU6050-collected data (on-site dataset collection)
- [ ] Verify Ollama-backed recommendation quality with a real running Ollama instance
- [ ] Consider adding an analog sound sensor (ADC-based) or JMISC audio path to restore an acoustic channel
- [ ] CI (GitHub Actions) for backend/frontend/simulation lint+test

---

## 10. Integration Notes

**Shared JSON schema** (MQTT payload, identical in both modes):
```json
{"machine_id": "Lathe-01", "timestamp": "2026-07-11T14:38:18+05:30", "health": "Warning", "fault": "Bearing Wear", "confidence": 0.94, "anomaly_score": 0.81}
```

**MQTT topics**: `plant/{machine_id}/telemetry` (QoS 0, healthy heartbeat every 30s), `plant/{machine_id}/alert` (QoS 1, immediate on any non-Healthy reading), `plant/{machine_id}/status` (QoS 1, retained, `online`/`offline`, backed by LWT on both the real Python brick and the simulator's publisher).

**REST endpoints**: see §4 table.

**WebSocket events**: `telemetry:update`, `alert:new`, `machine:status`, `recommendation:ready` — all pushed from `backend/app/websocket/manager.py`, triggered exclusively by `backend/app/mqtt/subscriber.py` and `backend/app/services/llm_manager.py`.

**Database relationships**: `Machine 1--* Telemetry`, `Machine 1--* Alert`, `Alert 1--1 Recommendation` (see `backend/app/db/models.py`).

**Shared interfaces**:
- `IDataSource` (`simulation/core/i_data_source.py`) — `ArduinoDataSource` vs `MachineSimulatorDataSource`, selected solely by `config.yaml`'s `mode` key, read in `simulation/main.py`'s `_build_data_source()`.
- Feature vector contract between MCU and Python brick: comma-separated string of 5 floats (mean, rms, peak, crestFactor, kurtosis), sent via `Bridge.call("run_inference", csv_string)`, returning an int status code (0=Healthy, 1=Warning, 2=Critical).
- ML calibration contract: `machine-learning/models/exported/calibration.json` is the single source for feature mean/std and warning/critical thresholds; it must stay in sync across `firmware/.../SignalProcessor.cpp`, `firmware/.../Config.h`, `firmware/.../python/config.py`, and `simulation/simulator/health_state_generator.py` (all four currently hardcode the same real values — see `docs/MODEL_TRAINING_REPORT.md` if retraining).

---

## 11. Repository Structure

```
Yantra_Rakshak_/
├── PROJECT_PROGRESS.md              # this file
├── config.yaml                      # MODE switch (hardware | simulation)
├── .gitignore
├── database/
│   └── yantrarakshak.db             # runtime SQLite file (gitignored)
├── docs/
│   ├── ARDUINO_UNO_Q_API_VERIFICATION.md
│   ├── BUILD_INSTRUCTIONS.md
│   ├── COMPILE_VERIFICATION.md
│   ├── FIRMWARE_ARCHITECTURE.md
│   ├── INSTALLATION_GUIDE.md
│   ├── MEMORY_AND_CPU_ESTIMATE.md
│   ├── MODEL_TRAINING_REPORT.md
│   ├── PYTHON_VERIFICATION.md
│   ├── REQUIRED_LIBRARIES.md
│   ├── SIMULATION_MODE.md
│   ├── VALIDATION_REPORT.md
│   └── WIRING_DIAGRAM.md
├── firmware/YantraRakshak/
│   ├── app.yaml
│   ├── sketch/                      # MCU (Zephyr) side
│   │   ├── sketch.ino, sketch.yaml
│   │   └── src/{config,utils,buffer,sensors,signal,bridge,led}/...
│   ├── python/                      # Qualcomm Linux (MPU) side
│   │   ├── main.py, config.py, requirements.txt, test_offline_verification.py
│   │   └── model/autoencoder_int8.tflite
│   └── experimental-mcu-inference/  # non-default on-MCU TFLM path
│       └── ml/{AnomalyDetector,model_data}.{h,cpp}
├── machine-learning/
│   ├── training/train_autoencoder.py
│   ├── models/exported/{autoencoder_int8.tflite, calibration.json}
│   └── requirements.txt
├── backend/
│   ├── app/
│   │   ├── main.py, config.py
│   │   ├── db/{database.py, models.py}
│   │   ├── mqtt/subscriber.py
│   │   ├── websocket/manager.py
│   │   ├── services/{machine_manager,history_manager,alert_manager,llm_manager}.py
│   │   └── api/{machines,alerts,recommendations,system}.py
│   ├── requirements.txt, .env.example
├── frontend/
│   ├── src/
│   │   ├── components/{common,alerts,simulation}/...
│   │   ├── pages/Dashboard.jsx
│   │   ├── services/{api.js, websocket.js}
│   │   ├── App.jsx, main.jsx, index.css
│   ├── package.json, vite.config.js, tailwind.config.js, postcss.config.js, index.html
└── simulation/
    ├── core/{i_data_source, arduino_data_source, machine_simulator_data_source}.py
    ├── simulator/{scenario_engine, sensor_noise_generator, fault_generator, virtual_sensors, health_state_generator, machine_simulator, simulation_controller}.py
    ├── publisher/data_publisher.py
    ├── config.py, main.py, requirements.txt
```

*(Not shown: `ml_env/`, `tools/`, `.venv/`, `node_modules/`, `__pycache__/` — local tooling/build artifacts, all gitignored.)*

---

## 12. Build & Run Instructions

### Full stack (Simulation Mode — no hardware needed)
```
# 1. MQTT broker (any broker works)
mosquitto -v
# (no Mosquitto installed in this dev environment; a pure-Python broker via
#  `pip install amqtt` was used instead for verification — see below)

# 2. Backend
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 3. Simulation (reads config.yaml's `mode` automatically)
cd simulation
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements.txt
python main.py

# 4. Frontend
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`.

### Switching to Hardware Mode
1. Set `mode: hardware` in root `config.yaml`.
2. Restart `simulation/main.py` — it becomes passive (`ArduinoDataSource`).
3. Flash `firmware/YantraRakshak/sketch/` to a real UNO Q per `docs/INSTALLATION_GUIDE.md` and `docs/BUILD_INSTRUCTIONS.md`.
4. Backend and frontend need **no changes or restarts**.

### Firmware build/verify only
```
cd firmware/YantraRakshak/sketch
arduino-cli core install arduino:zephyr
arduino-cli lib install "Adafruit MPU6050"
arduino-cli compile --fqbn arduino:zephyr:unoq .
```

### ML retraining
```
cd machine-learning
pip install -r requirements.txt
python training/train_autoencoder.py
```
Then propagate new `calibration.json` values into `SignalProcessor.cpp`, `Config.h`, `python/config.py`, and `simulation/simulator/health_state_generator.py` (see §10).

---

## 13. Changelog

- **2026-07-11**: Initial architecture, folder structure, dev environment, hardware architecture, firmware architecture + diagrams, TinyML pipeline math design, backend architecture (docs only), React dashboard design (docs only), local AI assistant design (docs only), master implementation roadmap — all chat-output design documents, no code yet.
- **2026-07-11**: Full monolithic Arduino firmware generated file-by-file (first pass) under `firmware/YantraRakshak/`, including a since-corrected assumption of on-MCU WiFi/MQTT/TFLM.
- **2026-07-11**: Resolved two integration blockers with real work: (a) verified every Arduino UNO Q API against official documentation and live compile testing, correcting the architecture to split MCU (sensing) vs. Python/Linux (inference + MQTT); (b) downloaded real CWRU Bearing Data Center data, trained and quantized a real autoencoder, generated real `model_data.cpp`/`.h`, and achieved a real successful `arduino-cli` compile. Added `docs/ARDUINO_UNO_Q_API_VERIFICATION.md`, `docs/MODEL_TRAINING_REPORT.md`, `docs/COMPILE_VERIFICATION.md`, `docs/PYTHON_VERIFICATION.md`, `docs/VALIDATION_REPORT.md`.
- **2026-07-11**: Added Software Simulation Mode per explicit requirement to leave firmware/TinyML/MQTT-schema/DB-schema untouched. Discovered backend/frontend didn't exist as code yet; built a minimal-but-real FastAPI backend and React frontend first, then the full `simulation/` module (`IDataSource` + `ArduinoDataSource` + `MachineSimulatorDataSource`, 4 machine profiles × 7 fault scenarios, gradual fault ramping, MQTT publisher matching the firmware's JSON schema exactly). Added root `config.yaml` as the single mode switch. Ran the entire stack live (broker, backend, simulation control API, frontend), injected a real fault, and screenshotted the dashboard showing correct real-time escalation. Added `docs/SIMULATION_MODE.md`.
- **2026-07-11**: Established `PROJECT_PROGRESS.md` as the standing living project log per explicit user instruction; updated `.gitignore` to exclude local venvs, node_modules, log files, and the runtime SQLite database.
- **2026-07-11**: Fixed the git remote (was pointed at a misspelled `Yantra_Raskhak_` repo with no real content) to `https://github.com/DivyanshSingh8899/Yantra_Rakshak_.git`; replaced the corrupted placeholder `README.md`; cleaned up non-deliverable dev artifacts; committed and pushed the entire project — first time the full codebase (firmware, ML pipeline, backend, frontend, simulation) is live on GitHub.
- **2026-07-11**: Frontend UI/UX pass — added `recharts`-based `TrendLineChart`/`Sparkline`, a hand-built SVG `HealthMeter` gauge, and a `FleetHeatmap`, all wired to the existing telemetry API; added a persisted dark/light theme toggle; added a new interactive `HardwareSetup` page (SVG wiring diagram for UNO Q + MPU6050 + RGB LED, hover/click-to-inspect, synced pin-reference table) driven by `src/data/wiringData.js`; made machine cards/heatmap cells open a `MachineDetailModal`. Verified live end-to-end in the Browser pane against the project's already-running backend/simulation (revived a stalled MQTT connection by restarting the broker) — no console errors, both themes and all new interactions confirmed working.
