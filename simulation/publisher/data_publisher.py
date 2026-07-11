"""
Data Publisher -- builds and publishes the EXACT JSON schema the real
Arduino firmware's AlertManager / python brick produce:

    {"machine_id": "...", "timestamp": "...", "health": "...",
     "fault": "...", "confidence": 0.0, "anomaly_score": 0.0}

to the same MQTT topics (plant/{machine_id}/telemetry|alert|status), with
the same publish-gating behavior: anomalous readings publish immediately
to the alert topic (QoS 1); healthy readings publish to the telemetry
topic only on a heartbeat interval (QoS 0) -- mirroring
firmware/YantraRakshak/python/main.py exactly so the backend's MQTT
subscriber cannot tell the two apart.
"""

import json
import time
from datetime import datetime, timedelta, timezone

import paho.mqtt.client as mqtt

from simulator.machine_simulator import SimulationTick

IST = timezone(timedelta(hours=5, minutes=30))
HEARTBEAT_INTERVAL_SECONDS = 30


class DataPublisher:
    def __init__(self, broker_host: str, broker_port: int, client_id: str = "yantra-rakshak-simulator"):
        self._client = mqtt.Client(client_id=client_id)
        self._broker_host = broker_host
        self._broker_port = broker_port
        self._connected = False
        self._last_heartbeat_at: dict[str, float] = {}

    def connect(self) -> None:
        self._client.connect(self._broker_host, self._broker_port, keepalive=60)
        self._client.loop_start()
        self._connected = True

    def disconnect(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()
        self._connected = False

    def publish_status(self, machine_id: str, status: str) -> None:
        if not self._connected:
            return
        self._client.publish(f"plant/{machine_id}/status", status, qos=1, retain=True)

    def publish_tick(self, tick: SimulationTick) -> None:
        if not self._connected:
            return

        payload = {
            "machine_id": tick.machine_id,
            "timestamp": datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S+05:30"),
            "health": tick.health_state.health,
            "fault": tick.health_state.fault,
            "confidence": tick.health_state.confidence,
            "anomaly_score": tick.health_state.anomaly_score,
        }

        is_anomalous = tick.health_state.health != "Healthy"
        now = time.monotonic()
        last_heartbeat = self._last_heartbeat_at.get(tick.machine_id, 0.0)
        heartbeat_due = (now - last_heartbeat) >= HEARTBEAT_INTERVAL_SECONDS

        if is_anomalous:
            self._client.publish(f"plant/{tick.machine_id}/alert", json.dumps(payload), qos=1)
        elif heartbeat_due:
            self._client.publish(f"plant/{tick.machine_id}/telemetry", json.dumps(payload), qos=0)
            self._last_heartbeat_at[tick.machine_id] = now
