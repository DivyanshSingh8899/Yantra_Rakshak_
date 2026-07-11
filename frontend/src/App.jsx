import { useEffect, useState } from "react";
import Dashboard from "./pages/Dashboard.jsx";
import HardwareSetup from "./pages/HardwareSetup.jsx";
import SimulationControlPanel from "./components/simulation/SimulationControlPanel.jsx";
import ThemeToggle from "./components/common/ThemeToggle.jsx";
import { useDarkMode } from "./hooks/useDarkMode.js";
import { api } from "./services/api.js";

const TABS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "hardware", label: "Hardware Setup" },
];

export default function App() {
  const [mode, setMode] = useState(null);
  const [theme, toggleTheme] = useDarkMode();
  const [activeTab, setActiveTab] = useState("dashboard");

  useEffect(() => {
    api.getSystemMode().then((res) => setMode(res.mode)).catch(() => setMode("unknown"));
  }, []);

  return (
    <div className="min-h-screen bg-surface-light dark:bg-surface-dark">
      <header className="flex items-center justify-between px-6 py-4 border-b border-black/10 dark:border-white/10">
        <div className="flex items-center gap-6">
          <h1 className="font-semibold text-[#0b0b0b] dark:text-white">YantraRakshak</h1>
          <nav className="flex items-center gap-1">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? "bg-black/10 dark:bg-white/15 text-[#0b0b0b] dark:text-white"
                    : "text-[#898781] hover:text-[#0b0b0b] dark:hover:text-white"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs rounded-full bg-black/5 dark:bg-white/10 px-3 py-1 text-[#52514e] dark:text-[#c3c2b7]">
            Mode: {mode || "..."}
          </span>
          <ThemeToggle theme={theme} onToggle={toggleTheme} />
        </div>
      </header>

      {activeTab === "dashboard" && (
        <>
          <Dashboard />
          <div className="px-6 pb-6">
            <SimulationControlPanel />
          </div>
        </>
      )}

      {activeTab === "hardware" && <HardwareSetup />}
    </div>
  );
}
