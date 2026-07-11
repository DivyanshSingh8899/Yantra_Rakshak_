import { useEffect, useState } from "react";
import { api } from "../../services/api.js";
import StatusBadge from "../common/StatusBadge.jsx";
import TrendLineChart from "../charts/TrendLineChart.jsx";
import HealthMeter from "../charts/HealthMeter.jsx";

export default function MachineDetailModal({ machine, onClose }) {
  const [telemetry, setTelemetry] = useState(null);

  useEffect(() => {
    if (!machine) return;
    setTelemetry(null);
    api.getMachineTelemetry(machine.machine_id).then(setTelemetry).catch(() => setTelemetry([]));

    const interval = setInterval(() => {
      api.getMachineTelemetry(machine.machine_id).then(setTelemetry).catch(() => {});
    }, 5000);
    return () => clearInterval(interval);
  }, [machine?.machine_id]);

  useEffect(() => {
    function onKeyDown(e) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  if (!machine) return null;

  const latestScore = telemetry && telemetry.length > 0 ? telemetry[telemetry.length - 1].reconstruction_error : null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 animate-[fadeIn_150ms_ease]"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-[#1a1a19] shadow-xl p-6 space-y-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-lg font-semibold text-[#0b0b0b] dark:text-white">{machine.name}</h3>
            <div className="text-xs text-[#898781] mt-0.5">
              {machine.machine_type || "unknown type"} &middot; {machine.location || "no location"}
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="rounded-full h-7 w-7 flex items-center justify-center text-[#898781] hover:bg-black/5 dark:hover:bg-white/10"
          >
            ×
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 items-center">
          <HealthMeter status={machine.health} score={latestScore} />
          <div className="sm:col-span-2 space-y-1 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-[#898781] w-24 shrink-0">Status</span>
              <StatusBadge status={machine.health} />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[#898781] w-24 shrink-0">Connection</span>
              <span className="text-[#0b0b0b] dark:text-white">{machine.status}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[#898781] w-24 shrink-0">Last seen</span>
              <span className="text-[#0b0b0b] dark:text-white">
                {machine.last_seen_at ? new Date(machine.last_seen_at).toLocaleString() : "never"}
              </span>
            </div>
          </div>
        </div>

        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-[#898781] mb-2">
            Anomaly score history
          </h4>
          {telemetry === null ? (
            <div className="text-sm text-[#898781] py-8 text-center">Loading telemetry…</div>
          ) : (
            <TrendLineChart data={telemetry} />
          )}
        </div>
      </div>
    </div>
  );
}
