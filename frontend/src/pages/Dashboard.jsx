import { useEffect, useState } from "react";
import StatTile from "../components/common/StatTile.jsx";
import MachineCard from "../components/alerts/MachineCard.jsx";
import AlertFeedItem from "../components/alerts/AlertFeedItem.jsx";
import { api } from "../services/api.js";
import { createRealtimeConnection } from "../services/websocket.js";

export default function Dashboard() {
  const [machines, setMachines] = useState([]);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    api.listMachines().then(setMachines).catch(() => {});
    api.getActiveAlerts().then(setAlerts).catch(() => {});

    const connection = createRealtimeConnection((message) => {
      if (message.event === "alert:new") {
        setAlerts((prev) => [message.alert, ...prev].slice(0, 50));
      }
      if (message.event === "machine:status" || message.event === "telemetry:update") {
        api.listMachines().then(setMachines).catch(() => {});
      }
    });

    return () => connection.close();
  }, []);

  const onlineCount = machines.filter((m) => m.status === "online").length;
  const activeAlertCount = alerts.filter((a) => a.status !== "resolved").length;

  return (
    <div className="p-6 space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatTile label="Total Machines" value={machines.length} />
        <StatTile label="Online" value={onlineCount} />
        <StatTile label="Active Alerts" value={activeAlertCount} />
        <StatTile
          label="Fleet Health"
          value={machines.every((m) => m.health === "healthy") ? "Healthy" : "Attention Needed"}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <h2 className="text-sm font-semibold text-[#52514e] dark:text-[#c3c2b7] mb-3">Machines</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {machines.map((machine) => (
              <MachineCard key={machine.machine_id} machine={machine} />
            ))}
            {machines.length === 0 && (
              <div className="text-sm text-[#898781]">
                No machines yet -- start the simulator or connect real hardware.
              </div>
            )}
          </div>
        </div>

        <div>
          <h2 className="text-sm font-semibold text-[#52514e] dark:text-[#c3c2b7] mb-3">Live Alert Feed</h2>
          <div className="rounded-lg border border-black/10 dark:border-white/10 bg-white dark:bg-[#1a1a19] p-4">
            {alerts.map((alert) => (
              <AlertFeedItem key={alert.alert_id} alert={alert} />
            ))}
            {alerts.length === 0 && <div className="text-sm text-[#898781]">No alerts yet.</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
