"""
WebSocket connection manager. Broadcasts the same six event types
regardless of data origin: telemetry:update, alert:new, alert:updated,
recommendation:ready, recommendation:failed, machine:status.

broadcast_sync() exists because the MQTT client (paho-mqtt) runs its
network loop in a plain background thread, not on the asyncio event loop
FastAPI's WebSocket connections live on -- it schedules the async
broadcast onto that loop via run_coroutine_threadsafe.
"""

import asyncio
import json

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Called once at FastAPI startup so background threads (the MQTT
        subscriber) have a loop to schedule broadcasts onto."""
        self._loop = loop

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        payload = json.dumps(message)
        stale = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                stale.append(connection)
        for connection in stale:
            self.disconnect(connection)

    def broadcast_sync(self, message: dict) -> None:
        if self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(self.broadcast(message), self._loop)


ws_manager = WebSocketManager()
