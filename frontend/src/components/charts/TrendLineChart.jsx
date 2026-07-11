import { Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

// Same calibration constants used by firmware/python/simulation (see
// machine-learning/models/exported/calibration.json) -- kept in sync manually,
// same as every other consumer of this contract (see PROJECT_PROGRESS.md §10).
const WARNING_THRESHOLD = 1.777191400527954;
const CRITICAL_THRESHOLD = 2.9144086837768555;

function formatTime(iso) {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export default function TrendLineChart({ data }) {
  if (!data || data.length === 0) {
    return <div className="text-sm text-[#898781] py-8 text-center">No telemetry history yet.</div>;
  }

  const chartData = data.map((d) => ({ ...d, time: formatTime(d.timestamp) }));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={chartData} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
        <XAxis dataKey="time" tick={{ fontSize: 11, fill: "#898781" }} minTickGap={30} />
        <YAxis tick={{ fontSize: 11, fill: "#898781" }} width={40} />
        <Tooltip
          contentStyle={{ fontSize: 12, borderRadius: 8 }}
          labelFormatter={(label) => `Time: ${label}`}
          formatter={(value) => [value?.toFixed?.(3) ?? value, "Anomaly score"]}
        />
        <ReferenceLine y={WARNING_THRESHOLD} stroke="#fab219" strokeDasharray="4 4" label={{ value: "Warning", fontSize: 10, fill: "#fab219", position: "insideTopLeft" }} />
        <ReferenceLine y={CRITICAL_THRESHOLD} stroke="#d03b3b" strokeDasharray="4 4" label={{ value: "Critical", fontSize: 10, fill: "#d03b3b", position: "insideTopLeft" }} />
        <Line
          type="monotone"
          dataKey="reconstruction_error"
          stroke="#3b82d0"
          strokeWidth={2}
          dot={false}
          isAnimationActive={true}
          animationDuration={400}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
