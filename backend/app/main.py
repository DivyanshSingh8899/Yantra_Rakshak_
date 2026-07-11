"""
FastAPI application entry point. Starts the DB, the mode-agnostic MQTT
subscriber, and the REST/WebSocket API. Whether the MQTT messages it
receives came from real Arduino UNO Q hardware or simulation/ is invisible
to everything in this file.
"""

import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api import alerts, machines, recommendations, system
from app.db.database import init_db
from app.mqtt.subscriber import mqtt_subscriber_service
from app.websocket.manager import ws_manager

app = FastAPI(title="YantraRakshak Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(machines.router)
app.include_router(alerts.router)
app.include_router(recommendations.router)
app.include_router(system.router)


@app.on_event("startup")
async def on_startup():
    init_db()
    ws_manager.bind_loop(asyncio.get_running_loop())
    mqtt_subscriber_service.start()


@app.on_event("shutdown")
async def on_shutdown():
    mqtt_subscriber_service.stop()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # This endpoint is server-push only; we still need to await
            # something so the connection registers as open and we notice
            # a client disconnect.
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
