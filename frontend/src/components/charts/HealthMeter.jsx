const STATUS_ANGLE = { healthy: 30, warning: 90, critical: 150 };
const STATUS_LABEL = { healthy: "Healthy", warning: "Warning", critical: "Critical" };

function polarToCartesian(cx, cy, r, angleDeg) {
  const angleRad = ((180 - angleDeg) * Math.PI) / 180;
  return { x: cx + r * Math.cos(angleRad), y: cy - r * Math.sin(angleRad) };
}

/** Semi-circle gauge showing a machine's current classified health state. */
export default function HealthMeter({ status, score }) {
  const key = status?.toLowerCase() in STATUS_ANGLE ? status.toLowerCase() : "healthy";
  const angle = STATUS_ANGLE[key];
  const cx = 90;
  const cy = 90;
  const r = 70;
  const needleTip = polarToCartesian(cx, cy, r - 10, angle);
  const needleColor = key === "critical" ? "#d03b3b" : key === "warning" ? "#fab219" : "#0ca30c";

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 180 100" className="w-full max-w-[220px]">
        <path d="M 20 90 A 70 70 0 0 1 80 21.5" fill="none" stroke="#0ca30c" strokeWidth="14" strokeLinecap="round" />
        <path d="M 76 20 A 70 70 0 0 1 104 20" fill="none" stroke="#fab219" strokeWidth="14" strokeLinecap="round" />
        <path d="M 100 21.5 A 70 70 0 0 1 160 90" fill="none" stroke="#d03b3b" strokeWidth="14" strokeLinecap="round" />
        <line
          x1={cx}
          y1={cy}
          x2={needleTip.x}
          y2={needleTip.y}
          stroke={needleColor}
          strokeWidth="3"
          strokeLinecap="round"
          style={{ transition: "all 400ms ease" }}
        />
        <circle cx={cx} cy={cy} r="5" fill={needleColor} />
      </svg>
      <div className="text-center -mt-2">
        <div className="text-lg font-semibold" style={{ color: needleColor }}>
          {STATUS_LABEL[key]}
        </div>
        {score !== undefined && score !== null && (
          <div className="text-xs text-[#898781]">anomaly score {score.toFixed(3)}</div>
        )}
      </div>
    </div>
  );
}
