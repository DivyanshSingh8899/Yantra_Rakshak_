import { useState } from "react";
import { ALL_PINS, BOARD_PINS, CONNECTIONS, LED_PINS, MPU6050_PINS } from "../data/wiringData.js";

function findPin(id) {
  return ALL_PINS.find((p) => p.id === id);
}

export default function HardwareSetup() {
  const [activeId, setActiveId] = useState(null);
  const active = CONNECTIONS.find((c) => c.id === activeId) || null;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[#0b0b0b] dark:text-white">Arduino UNO Q — Hardware Setup</h2>
        <p className="mt-1 text-sm text-[#52514e] dark:text-[#c3c2b7] max-w-2xl">
          MPU6050 vibration sensor and RGB status LED wiring for the physical build. Hover or click any
          connection to see details. Pin assignments match{" "}
          <code className="text-xs bg-black/5 dark:bg-white/10 rounded px-1 py-0.5">
            firmware/YantraRakshak/sketch/src/config/Config.h
          </code>
          .
        </p>
        <div className="mt-2 inline-flex items-center gap-1.5 text-xs text-status-warning">
          <span className="h-1.5 w-1.5 rounded-full bg-status-warning" />
          Firmware code-complete and compiled — awaiting physical hardware for flash/run verification.
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-[#1a1a19] p-4">
          <svg viewBox="0 0 620 420" className="w-full h-auto select-none">
            {/* Boards */}
            <rect x="30" y="60" width="120" height="320" rx="10" className="fill-black/5 dark:fill-white/5" stroke="#898781" strokeWidth="1" />
            <text x="90" y="45" textAnchor="middle" className="fill-[#52514e] dark:fill-[#c3c2b7] text-[13px] font-medium">
              Arduino UNO Q
            </text>

            <rect x="470" y="40" width="120" height="190" rx="10" className="fill-black/5 dark:fill-white/5" stroke="#898781" strokeWidth="1" />
            <text x="530" y="25" textAnchor="middle" className="fill-[#52514e] dark:fill-[#c3c2b7] text-[13px] font-medium">
              MPU6050
            </text>

            <rect x="470" y="250" width="120" height="130" rx="10" className="fill-black/5 dark:fill-white/5" stroke="#898781" strokeWidth="1" />
            <text x="530" y="235" textAnchor="middle" className="fill-[#52514e] dark:fill-[#c3c2b7] text-[13px] font-medium">
              RGB LED
            </text>

            {/* Connections */}
            {CONNECTIONS.map((c) => {
              const to = findPin(c.to);
              if (!c.from) {
                return (
                  <circle
                    key={c.id}
                    cx={to.x}
                    cy={to.y}
                    r={activeId === c.id ? 7 : 5}
                    fill="none"
                    stroke={c.color}
                    strokeDasharray="2 2"
                    strokeWidth={activeId === c.id ? 2 : 1.5}
                    onMouseEnter={() => setActiveId(c.id)}
                    onMouseLeave={() => setActiveId((id) => (id === c.id ? null : id))}
                    onClick={() => setActiveId(c.id)}
                    className="cursor-pointer"
                  />
                );
              }
              const from = findPin(c.from);
              const isActive = activeId === c.id;
              return (
                <line
                  key={c.id}
                  x1={from.x}
                  y1={from.y}
                  x2={to.x}
                  y2={to.y}
                  stroke={c.color}
                  strokeWidth={isActive ? 4 : 2}
                  opacity={activeId && !isActive ? 0.25 : 1}
                  onMouseEnter={() => setActiveId(c.id)}
                  onMouseLeave={() => setActiveId((id) => (id === c.id ? null : id))}
                  onClick={() => setActiveId(c.id)}
                  className="cursor-pointer transition-all"
                />
              );
            })}

            {/* Pins */}
            {[...BOARD_PINS, ...MPU6050_PINS, ...LED_PINS].map((p) => (
              <g key={p.id}>
                <circle cx={p.x} cy={p.y} r="4" className="fill-[#0b0b0b] dark:fill-white" />
                <text
                  x={p.x < 300 ? p.x - 10 : p.x + 10}
                  y={p.y + 4}
                  textAnchor={p.x < 300 ? "end" : "start"}
                  className="fill-[#52514e] dark:fill-[#c3c2b7] text-[11px]"
                >
                  {p.label}
                </text>
              </g>
            ))}
          </svg>
        </div>

        <div className="space-y-4">
          <div className="rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-[#1a1a19] p-4 min-h-[140px]">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-[#898781] mb-2">
              Connection details
            </h3>
            {active ? (
              <div>
                <div className="flex items-center gap-2 font-medium text-[#0b0b0b] dark:text-white">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: active.color }} />
                  {active.label}
                </div>
                <p className="mt-2 text-sm text-[#52514e] dark:text-[#c3c2b7]">{active.note}</p>
              </div>
            ) : (
              <p className="text-sm text-[#898781]">Hover or click a wire to see its purpose.</p>
            )}
          </div>

          <div className="rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-[#1a1a19] p-4">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-[#898781] mb-2">Power</h3>
            <ul className="text-sm text-[#52514e] dark:text-[#c3c2b7] space-y-1.5 list-disc list-inside">
              <li>Development/flashing: USB-C from the laptop is sufficient.</li>
              <li>
                Sustained operation (Linux side booted, Wi-Fi active, Python brick running): use the
                board's DC input (7–24V) or a robust USB-C power source — a thin laptop USB port may not
                sustain the full dual-processor load.
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-[#1a1a19] p-4 overflow-x-auto">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-[#898781] mb-3">
          Full pin reference
        </h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-[#898781] border-b border-black/10 dark:border-white/10">
              <th className="py-2 pr-4">Connection</th>
              <th className="py-2 pr-4">UNO Q pin</th>
              <th className="py-2">Notes</th>
            </tr>
          </thead>
          <tbody>
            {CONNECTIONS.map((c) => (
              <tr
                key={c.id}
                onMouseEnter={() => setActiveId(c.id)}
                onMouseLeave={() => setActiveId((id) => (id === c.id ? null : id))}
                className={`border-b border-black/5 dark:border-white/5 last:border-0 cursor-pointer ${
                  activeId === c.id ? "bg-black/5 dark:bg-white/5" : ""
                }`}
              >
                <td className="py-2 pr-4 text-[#0b0b0b] dark:text-white flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full shrink-0" style={{ backgroundColor: c.color }} />
                  {c.label}
                </td>
                <td className="py-2 pr-4 text-[#52514e] dark:text-[#c3c2b7]">
                  {c.from ? findPin(c.from).label : "—"}
                </td>
                <td className="py-2 text-[#898781]">{c.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
