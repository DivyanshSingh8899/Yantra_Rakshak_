const COLOR_BY_STATUS = {
  healthy: "bg-status-good",
  warning: "bg-status-warning",
  critical: "bg-status-critical",
  unknown: "bg-gray-400",
};

/** At-a-glance fleet-wide grid, one cell per machine, colored by health status. */
export default function FleetHeatmap({ machines, onSelect }) {
  if (!machines || machines.length === 0) {
    return <div className="text-sm text-[#898781]">No machines to display yet.</div>;
  }

  return (
    <div>
      <div className="grid grid-cols-6 sm:grid-cols-8 md:grid-cols-10 gap-2">
        {machines.map((m) => {
          const color = COLOR_BY_STATUS[m.health?.toLowerCase()] || COLOR_BY_STATUS.unknown;
          return (
            <button
              key={m.machine_id}
              onClick={() => onSelect?.(m)}
              title={`${m.name} · ${m.health}`}
              className={`aspect-square rounded ${color} opacity-80 hover:opacity-100 hover:scale-110 transition-all focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-black/30 dark:focus:ring-white/40`}
            />
          );
        })}
      </div>
      <div className="mt-3 flex flex-wrap gap-4 text-xs text-[#898781]">
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-sm bg-status-good" /> Healthy
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-sm bg-status-warning" /> Warning
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-sm bg-status-critical" /> Critical
        </span>
      </div>
    </div>
  );
}
