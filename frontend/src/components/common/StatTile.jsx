export default function StatTile({ label, value, sublabel }) {
  return (
    <div className="rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-[#1a1a19] p-4">
      <div className="text-xs text-[#898781] uppercase tracking-wide">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-[#0b0b0b] dark:text-white">{value}</div>
      {sublabel && <div className="mt-1 text-xs text-[#52514e] dark:text-[#c3c2b7]">{sublabel}</div>}
    </div>
  );
}
