import { useEffect, useState } from "react";
import Dashboard from "./pages/Dashboard.jsx";
import SimulationControlPanel from "./components/simulation/SimulationControlPanel.jsx";
import { api } from "./services/api.js";

export default function App() {
  const [mode, setMode] = useState(null);

  useEffect(() => {
    api.getSystemMode().then((res) => setMode(res.mode)).catch(() => setMode("unknown"));
  }, []);

  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between px-6 py-4 border-b border-black/10 dark:border-white/10">
        <h1 className="font-semibold text-[#0b0b0b] dark:text-white">YantraRakshak</h1>
        <span className="text-xs rounded-full bg-black/5 dark:bg-white/10 px-3 py-1 text-[#52514e] dark:text-[#c3c2b7]">
          Mode: {mode || "..."}
        </span>
      </header>

      <Dashboard />

      <div className="px-6 pb-6">
        <SimulationControlPanel />
      </div>
    </div>
  );
}
