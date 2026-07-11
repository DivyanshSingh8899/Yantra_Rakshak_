"""
MQTT Subscriber -- the module that makes "the backend cannot distinguish
Hardware Mode from Simulation Mode" true by construction. It subscribes to
plant/+/telemetry, plant/+/alert, and plant/+/status and parses exactly the
JSON schema the real Arduino firmware's AlertManager/python brick produces:

    {"machine_id": "...", "timestamp": "...", "health": "...",
     "fault": "...", "confidence": 0.0, "anomaly_score": 0.0}

The simulator (simulation/publisher/data_publisher.py) publishes the
identical schema to the identical topics. This file has no branch, flag,
or import that references "simulation" or "hardware" anywhere -- that is
the point.
"""

import json
import threading
from datetime import datetime

import paho.mqtt.client as mqtt

from app.config import settings
from app.db.database import session_scope
from app.services.alert_manager import AlertManager
from app.services.history_manager import HistoryManager
from app.services.llm_manager import LLMManager
from app.services.machine_manager import MachineManager
from app.websocket.manager import ws_manager

TOPIC_TELEMETRY = "plant/+/telemetry"
TOPIC_ALERT = "plant/+/alert"
TOPIC_STATUS = "plant/+/status"


def _machine_id_from_topic(topic: str) -> str:
    # plant/{machine_id}/telemetry|alert|status
    return topic.split("/")[1]


def _parse_timestamp(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return datetime.utcnow()


class MqttSubscriberService:
    def __init__(self):
        self._client = mqtt.Client(client_id="yantra-rakshak-backend")
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._client.connect(settings.mqtt_broker_host, settings.mqtt_broker_port, keepalive=60)
        self._thread = threading.Thread(target=self._client.loop_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._client.disconnect()

    def _on_connect(self, client, userdata, flags, rc):
        client.subscribe(
            [(TOPIC_TELEMETRY, 0), (TOPIC_ALERT, 1), (TOPIC_STATUS, 1)]
        )

    def _on_message(self, client, userdata, msg):
        machine_id = _machine_id_from_topic(msg.topic)

        if msg.topic.endswith("/status"):
            self._handle_status(machine_id, msg.payload.decode("utf-8"))
            return

        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return

        if msg.topic.endswith("/telemetry"):
            self._handle_telemetry(machine_id, payload)
        elif msg.topic.endswith("/alert"):
            self._handle_alert(machine_id, payload)

    def _handle_status(self, machine_id: str, payload: str) -> None:
        with session_scope() as db:
            MachineManager(db).update_status(machine_id, payload)
        ws_manager.broadcast_sync({"event": "machine:status", "machine_id": machine_id, "status": payload})

    def _handle_telemetry(self, machine_id: str, payload: dict) -> None:
        with session_scope() as db:
            MachineManager(db).touch_last_seen(machine_id)
            HistoryManager(db).store_telemetry(
                machine_id=machine_id,
                timestamp=_parse_timestamp(payload.get("timestamp")),
                reconstruction_error=payload.get("anomaly_score"),
                raw_payload=json.dumps(payload),
            )
        ws_manager.broadcast_sync({"event": "telemetry:update", "machine_id": machine_id, "payload": payload})

    def _handle_alert(self, machine_id: str, payload: dict) -> None:
        severity = str(payload.get("health", "warning")).lower()
        with session_scope() as db:
            MachineManager(db).touch_last_seen(machine_id)
            alert = AlertManager(db).create_alert(
                machine_id=machine_id,
                triggered_at=_parse_timestamp(payload.get("timestamp")),
                severity=severity,
                classification=payload.get("fault"),
                confidence=payload.get("confidence"),
                reconstruction_error=payload.get("anomaly_score"),
            )
            alert_id = alert.alert_id
            alert_payload = {
                "alert_id": alert.alert_id,
                "machine_id": alert.machine_id,
                "severity": alert.severity,
                "classification": alert.classification,
                "confidence": alert.confidence,
                "anomaly_score": alert.reconstruction_error,
                "triggered_at": alert.triggered_at.isoformat(),
            }

        ws_manager.broadcast_sync({"event": "alert:new", "alert": alert_payload})

        with session_scope() as db:
            recommendation = LLMManager(db).generate_recommendation(alert_id)
            rec_payload = {
                "alert_id": alert_id,
                "recommendation_text": recommendation.recommendation_text,
                "generation_status": recommendation.generation_status,
            }
        ws_manager.broadcast_sync({"event": "recommendation:ready", "recommendation": rec_payload})


mqtt_subscriber_service = MqttSubscriberService()
