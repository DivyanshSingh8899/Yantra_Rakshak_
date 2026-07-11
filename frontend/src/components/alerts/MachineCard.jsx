import { useEffect, useState } from "react";
import StatusBadge from "../common/StatusBadge.jsx";
import Sparkline from "../charts/Sparkline.jsx";
import { api } from "../../services/api.js";

export default function MachineCard({ machine, onSelect }) {
  const [telemetry, setTelemetry] = useState(null);

  useEffect(() => {
    api.getMachineTelemetry(machine.machine_id).then(setTelemetry).catch(() => setTelemetry([]));
  }, [machine.machine_id, machine.last_seen_at]);

  return (
    <button
      onClick={() => onSelect?.(machine)}
      className="text-left w-full rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-[#1a1a19] p-4 transition-all hover:shadow-md hover:-translate-y-0.5 hover:border-black/20 dark:hover:border-white/20 focus:outline-none focus:ring-2 focus:ring-black/20 dark:focus:ring-white/30"
    >
      <div className="flex items-center justify-between">
        <div className="font-medium text-[#0b0b0b] dark:text-white">{machine.name}</div>
        <StatusBadge status={machine.health} />
      </div>
      <div className="mt-2 text-xs text-[#898781]">
        {machine.machine_type || "unknown type"} &middot; {machine.status}
      </div>
      <div className="mt-1 text-xs text-[#898781]">
        Last seen: {machine.last_seen_at ? new Date(machine.last_seen_at).toLocaleString() : "never"}
      </div>
      <div className="mt-2">
        <Sparkline data={telemetry} status={machine.health} />
      </div>
    </button>
  );
}
