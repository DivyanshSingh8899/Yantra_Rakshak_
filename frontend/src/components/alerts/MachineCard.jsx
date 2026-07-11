import StatusBadge from "../common/StatusBadge.jsx";

export default function MachineCard({ machine }) {
  return (
    <div className="rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-[#1a1a19] p-4">
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
    </div>
  );
}
