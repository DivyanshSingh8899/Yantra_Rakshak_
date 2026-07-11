"""
YantraRakshak MPU (Qualcomm Linux) side brick.

Registers "run_inference" for the MCU sketch to call (via
Arduino_RouterBridge) once per completed 128-sample vibration window,
runs the real trained INT8 autoencoder (see model/autoencoder_int8.tflite
and docs/MODEL_TRAINING_REPORT.md), classifies Healthy/Warning/Critical,
publishes the JSON alert/heartbeat payload over MQTT, and returns a status
code to the MCU for its LED.

Bridge API used here (Bridge.provide / App.run) is confirmed from an
official Arduino UNO Q Person Detector "Bridge, Bricks, and Real-Time AI"
tutorial and the Arduino CLI blink example -- see
docs/ARDUINO_UNO_Q_API_VERIFICATION.md for exact sources. Python-side
Bridge.provide() specifically (as opposed to the confirmed MCU-side
Bridge.provide()/Bridge.call() pair) is the one part of this file inferred
from the router's documented bidirectional "star topology" design rather
than a directly-quoted Python example -- verify against
docs.arduino.cc/tutorials/uno-q/routerbridge-multilanguage on real
hardware before shipping.
"""

import json
import time
from datetime import datetime, timezone, timedelta

import numpy as np
import paho.mqtt.client as mqtt

try:
    from tflite_runtime.interpreter import Interpreter
except ImportError:
    import tensorflow as tf
    Interpreter = tf.lite.Interpreter

from arduino.app_utils import Bridge, App

import config

IST = timezone(timedelta(hours=5, minutes=30))

_interpreter = Interpreter(model_path=config.MODEL_PATH)
_interpreter.allocate_tensors()
_input_details = _interpreter.get_input_details()[0]
_output_details = _interpreter.get_output_details()[0]
_input_scale, _input_zero_point = _input_details["quantization"]
_output_scale, _output_zero_point = _output_details["quantization"]

_mqtt_client = mqtt.Client(client_id=config.MQTT_CLIENT_ID)
_mqtt_client.will_set(config.MQTT_STATUS_TOPIC, config.MQTT_STATUS_OFFLINE_PAYLOAD, qos=1, retain=True)

_last_status_code = 0
_last_payload = None


def _connect_mqtt():
    _mqtt_client.connect(config.MQTT_BROKER_HOST, config.MQTT_BROKER_PORT, config.MQTT_KEEPALIVE_SECONDS)
    _mqtt_client.publish(config.MQTT_STATUS_TOPIC, config.MQTT_STATUS_ONLINE_PAYLOAD, qos=1, retain=True)
    _mqtt_client.loop_start()


def _classify(anomaly_score: float) -> int:
    if anomaly_score > config.CRITICAL_THRESHOLD:
        return 2
    if anomaly_score > config.WARNING_THRESHOLD:
        return 1
    return 0


def _health_label(status_code: int) -> str:
    return {0: "Healthy", 1: "Warning", 2: "Critical"}[status_code]


def _confidence(status_code: int, anomaly_score: float) -> float:
    if status_code == 0:
        ratio = anomaly_score / config.WARNING_THRESHOLD
        return max(0.0, 1.0 - min(ratio, 1.0))
    if status_code == 1:
        span = config.CRITICAL_THRESHOLD - config.WARNING_THRESHOLD
        progress = (anomaly_score - config.WARNING_THRESHOLD) / span
        return min(max(progress, 0.0), 1.0)
    ratio = anomaly_score / config.CRITICAL_THRESHOLD
    return min(ratio, 1.0)


def _fault_label(status_code: int, dominant_feature_index: int) -> str:
    # This model is a single fault-vs-normal detector trained only on CWRU
    # bearing fault recordings (inner race + ball faults) -- it was never
    # trained to discriminate between different fault *types*. Reporting
    # invented fault-type names per dominant feature would fabricate a
    # distinction the model cannot actually make, so every anomaly is
    # reported as one honest label, with the statistically dominant
    # feature named as supporting diagnostic detail only.
    if status_code == 0:
        return "None"
    feature_name = config.FEATURE_NAMES[dominant_feature_index]
    return f"Bearing Fault Signature ({feature_name}-dominant)"


def run_inference(features_csv: str) -> int:
    global _last_status_code, _last_payload

    features = np.array([float(v) for v in features_csv.split(",")], dtype=np.float32)

    quantized = np.round(features / _input_scale + _input_zero_point)
    quantized = np.clip(quantized, -128, 127).astype(np.int8)
    _interpreter.set_tensor(_input_details["index"], quantized.reshape(1, -1))
    _interpreter.invoke()
    raw_output = _interpreter.get_tensor(_output_details["index"])[0]
    reconstructed = (raw_output.astype(np.float32) - _output_zero_point) * _output_scale

    errors = (features - reconstructed) ** 2
    anomaly_score = float(np.mean(errors))
    dominant_feature_index = int(np.argmax(errors))

    status_code = _classify(anomaly_score)
    confidence = _confidence(status_code, anomaly_score)

    payload = {
        "machine_id": config.MACHINE_ID,
        "timestamp": datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S+05:30"),
        "health": _health_label(status_code),
        "fault": _fault_label(status_code, dominant_feature_index),
        "confidence": round(confidence, 4),
        "anomaly_score": round(anomaly_score, 4),
    }

    topic = config.MQTT_ALERT_TOPIC if status_code != 0 else config.MQTT_TELEMETRY_TOPIC
    qos = 1 if status_code != 0 else 0
    _mqtt_client.publish(topic, json.dumps(payload), qos=qos)

    _last_status_code = status_code
    _last_payload = payload

    return status_code


def _heartbeat_loop():
    """Publishes the last known status on the telemetry topic every
    HEARTBEAT_INTERVAL_SECONDS, independent of the MCU's per-window calls,
    so the backend can detect a silent/stalled MCU even when it is not
    reporting anomalies.

    Matches the confirmed App.run(user_loop=...) pattern from Arduino's own
    UNO Q Bridge blink example: App.run() itself calls this function
    repeatedly, so it must sleep once and return each call rather than
    looping internally -- an internal `while True` here would block
    App.run's own cycle forever on the first call."""
    time.sleep(config.HEARTBEAT_INTERVAL_SECONDS)
    if _last_payload is not None:
        _mqtt_client.publish(config.MQTT_TELEMETRY_TOPIC, json.dumps(_last_payload), qos=0)


_connect_mqtt()
Bridge.provide("run_inference", run_inference)

App.run(user_loop=_heartbeat_loop)
