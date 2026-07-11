import { useEffect, useState } from "react";

const SIM_API_BASE_URL = import.meta.env.VITE_SIMULATION_API_BASE_URL || "http://localhost:8001";

const MACHINE_TYPES = ["electric_motor", "water_pump", "air_compressor", "lathe"];
const SCENARIOS = [
  "healthy",
  "bearing_wear",
  "misalignment",
  "lubrication_failure",
  "motor_imbalance",
  "overheating",
  "critical_failure",
];
// The backend only understands the specific fault names above -- there's no
// "unhealthy" scenario server-side. The Scenario selector below simplifies
// to a healthy/unhealthy choice for the user; picking "unhealthy" randomly
// selects one of these specific faults when the simulation starts.
const FAULT_SCENARIOS = SCENARIOS.filter((s) => s !== "healthy");

async function simRequest(path, options = {}) {
  const response = await fetch(`${SIM_API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) throw new Error(`Simulation API error ${response.status}`);
  return response.json();
}

/**
 * Simulation Control Panel -- the only new UI this feature adds. Talks
 * directly to simulation/main.py's own small control API (default
 * localhost:8001), not the main backend -- these are simulator control
 * commands, not machine telemetry, so they don't belong in the
 * mode-agnostic backend API.
 */
export default function SimulationControlPanel() {
  const [state, setState] = useState(null);
  const [machineId, setMachineId] = useState("Motor-01");
  const [machineType, setMachineType] = useState(MACHINE_TYPES[0]);
  const [scenario, setScenario] = useState("healthy");
  const [speed, setSpeed] = useState(1.0);
  const [error, setError] = useState(null);

  const refreshState = () => {
    simRequest("/simulation/state")
      .then(setState)
      .catch((e) => setError(e.message));
  };

  useEffect(() => {
    refreshState();
    const interval = setInterval(refreshState, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleStart = () => {
    const actualScenario =
      scenario === "healthy" ? "healthy" : FAULT_SCENARIOS[Math.floor(Math.random() * FAULT_SCENARIOS.length)];
    return simRequest("/simulation/start", {
      method: "POST",
      body: JSON.stringify({ machine_id: machineId, machine_type: machineType, scenario: actualScenario }),
    }).then(refreshState).catch((e) => setError(e.message));
  };

  const handlePause = () =>
    simRequest("/simulation/pause", { method: "POST" }).then(refreshState).catch((e) => setError(e.message));

  const handleResume = () =>
    simRequest("/simulation/resume", { method: "POST" }).then(refreshState).catch((e) => setError(e.message));

  const handleSpeedChange = (value) => {
    setSpeed(value);
    simRequest("/simulation/speed", {
      method: "POST",
      body: JSON.stringify({ speed: value }),
    }).catch((e) => setError(e.message));
  };

  const handleInjectFault = (faultScenario) =>
    simRequest("/simulation/inject-fault", {
      method: "POST",
      body: JSON.stringify({ scenario: faultScenario }),
    }).then(refreshState).catch((e) => setError(e.message));

  return (
    <div className="rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-[#1a1a19] p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-[#52514e] dark:text-[#c3c2b7]">Simulation Control Panel</h2>
        <span className="text-xs text-[#898781]">
          {state ? (state.running ? (state.paused ? "Paused" : "Running") : "Stopped") : "..."}
        </span>
      </div>

      {error && <div className="text-xs text-status-critical">{error}</div>}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <label className="text-xs text-[#898781]">
          Machine ID
          <input
            className="mt-1 w-full rounded border border-black/10 dark:border-white/10 bg-transparent p-2 text-sm"
            value={machineId}
            onChange={(e) => setMachineId(e.target.value)}
          />
        </label>

        <label className="text-xs text-[#898781]">
          Machine Type
          <select
            className="mt-1 w-full rounded border border-black/10 dark:border-white/10 bg-transparent p-2 text-sm"
            value={machineType}
            onChange={(e) => setMachineType(e.target.value)}
          >
            {MACHINE_TYPES.map((type) => (
              <option key={type} value={type}>
                {type.replace("_", " ")}
              </option>
            ))}
          </select>
        </label>

        <label className="text-xs text-[#898781]">
          Scenario
          <select
            className={`mt-1 w-full rounded border bg-transparent p-2 text-sm font-medium ${
              scenario === "healthy"
                ? "border-status-good/40 text-status-good"
                : "border-status-critical/40 text-status-critical"
            }`}
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
          >
            <option value="healthy" style={{ color: "#0ca30c" }}>
              Healthy
            </option>
            <option value="unhealthy" style={{ color: "#d03b3b" }}>
              Unhealthy
            </option>
          </select>
        </label>
      </div>

      <div className="flex flex-wrap gap-2">
        <button onClick={handleStart} className="rounded bg-status-good/10 text-status-good px-3 py-1.5 text-sm font-medium">
          Start
        </button>
        <button onClick={handlePause} className="rounded bg-status-warning/10 text-status-warning px-3 py-1.5 text-sm font-medium">
          Pause
        </button>
        <button onClick={handleResume} className="rounded bg-black/5 dark:bg-white/10 px-3 py-1.5 text-sm font-medium">
          Resume
        </button>
      </div>

      <label className="block text-xs text-[#898781]">
        Speed multiplier: {speed}x
        <input
          type="range"
          min="0.25"
          max="8"
          step="0.25"
          value={speed}
          onChange={(e) => handleSpeedChange(parseFloat(e.target.value))}
          className="mt-1 w-full"
        />
      </label>

      <div>
        <div className="text-xs text-[#898781] mb-1">Inject fault immediately</div>
        <div className="flex flex-wrap gap-2">
          {FAULT_SCENARIOS.map((s) => (
            <button
              key={s}
              onClick={() => handleInjectFault(s)}
              className="rounded border border-black/10 dark:border-white/10 px-2 py-1 text-xs"
            >
              {s.replace("_", " ")}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
