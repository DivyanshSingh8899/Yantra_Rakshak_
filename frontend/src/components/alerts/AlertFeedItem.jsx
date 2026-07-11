import StatusBadge from "../common/StatusBadge.jsx";

export default function AlertFeedItem({ alert }) {
  const timestamp = alert.triggered_at ? new Date(alert.triggered_at).toLocaleTimeString() : "";
  return (
    <div className="flex items-center justify-between border-b border-black/5 dark:border-white/5 py-2 text-sm">
      <div className="flex items-center gap-3">
        <StatusBadge status={alert.severity} />
        <span className="text-[#0b0b0b] dark:text-white">{alert.machine_id}</span>
        <span className="text-[#898781]">{alert.classification || "unclassified"}</span>
      </div>
      <span className="text-xs text-[#898781]">{timestamp}</span>
    </div>
  );
}
