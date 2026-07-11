import { Line, LineChart, ResponsiveContainer } from "recharts";

const STROKE_BY_STATUS = {
  healthy: "#0ca30c",
  warning: "#fab219",
  critical: "#d03b3b",
};

/** Compact, axis-free trend line for embedding inside a MachineCard. */
export default function Sparkline({ data, status }) {
  if (!data || data.length < 2) {
    return <div className="h-10 text-xs text-[#898781] flex items-center">Not enough data yet</div>;
  }
  const stroke = STROKE_BY_STATUS[status?.toLowerCase()] || "#898781";

  return (
    <ResponsiveContainer width="100%" height={40}>
      <LineChart data={data}>
        <Line type="monotone" dataKey="reconstruction_error" stroke={stroke} strokeWidth={1.5} dot={false} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
