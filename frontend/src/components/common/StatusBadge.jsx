const STATUS_STYLES = {
  healthy: { color: "text-status-good", dot: "bg-status-good", label: "Healthy" },
  warning: { color: "text-status-warning", dot: "bg-status-warning", label: "Warning" },
  critical: { color: "text-status-critical", dot: "bg-status-critical", label: "Critical" },
  unknown: { color: "text-gray-400", dot: "bg-gray-400", label: "Unknown" },
};

/** Status is always icon (dot) + label together -- never color alone. */
export default function StatusBadge({ status }) {
  const style = STATUS_STYLES[status?.toLowerCase()] || STATUS_STYLES.unknown;
  return (
    <span className={`inline-flex items-center gap-1.5 text-sm font-medium ${style.color}`}>
      <span className={`h-2 w-2 rounded-full ${style.dot}`} />
      {style.label}
    </span>
  );
}
