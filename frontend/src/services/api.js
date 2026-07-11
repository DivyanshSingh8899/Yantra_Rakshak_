const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${await response.text()}`);
  }
  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  listMachines: () => request("/api/v1/machines"),
  getMachine: (machineId) => request(`/api/v1/machines/${machineId}`),
  getMachineTelemetry: (machineId) => request(`/api/v1/machines/${machineId}/telemetry`),
  listAlerts: () => request("/api/v1/alerts"),
  getActiveAlerts: () => request("/api/v1/alerts/active"),
  acknowledgeAlert: (alertId) => request(`/api/v1/alerts/${alertId}/acknowledge`, { method: "POST" }),
  resolveAlert: (alertId) => request(`/api/v1/alerts/${alertId}/resolve`, { method: "POST" }),
  getRecommendation: (alertId) => request(`/api/v1/recommendations/${alertId}`),
  getSystemMode: () => request("/api/v1/system/mode"),
  getSystemHealth: () => request("/api/v1/system/health"),
};
