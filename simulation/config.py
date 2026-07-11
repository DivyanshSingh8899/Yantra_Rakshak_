"""
Simulation module configuration -- reads the single shared root
config.yaml. `mode` is the one value that decides whether main.py's
factory instantiates ArduinoDataSource or MachineSimulatorDataSource.
"""

from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONFIG_PATH = _REPO_ROOT / "config.yaml"


def load_config() -> dict:
    if not _CONFIG_PATH.exists():
        return {"mode": "hardware"}
    with open(_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f) or {"mode": "hardware"}


def get_mode() -> str:
    return load_config().get("mode", "hardware")


def get_mqtt_settings() -> tuple[str, int]:
    config = load_config()
    mqtt_config = config.get("mqtt", {})
    return mqtt_config.get("broker_host", "localhost"), int(mqtt_config.get("broker_port", 1883))


def get_default_machines() -> list[dict]:
    config = load_config()
    return config.get("simulation", {}).get("machines", [])


def get_default_scenario() -> str:
    config = load_config()
    return config.get("simulation", {}).get("default_scenario", "healthy")


def get_default_speed() -> float:
    config = load_config()
    return float(config.get("simulation", {}).get("default_speed_multiplier", 1.0))
