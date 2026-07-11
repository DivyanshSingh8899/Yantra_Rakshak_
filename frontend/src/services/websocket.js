const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws";

/**
 * Thin WebSocket wrapper with auto-reconnect. Dispatches every message to
 * all registered listeners regardless of its `event` field -- callers
 * filter for the events they care about. Identical whether the event
 * originated from real hardware telemetry or the simulator.
 */
export function createRealtimeConnection(onMessage) {
  let socket;
  let shouldReconnect = true;

  function connect() {
    socket = new WebSocket(WS_URL);
    socket.onmessage = (event) => {
      try {
        onMessage(JSON.parse(event.data));
      } catch {
        // ignore malformed frames
      }
    };
    socket.onclose = () => {
      if (shouldReconnect) {
        setTimeout(connect, 2000);
      }
    };
  }

  connect();

  return {
    close() {
      shouldReconnect = false;
      socket?.close();
    },
  };
}
