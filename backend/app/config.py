"""
Backend configuration: loads the shared root config.yaml (for the
mode/mqtt/llm settings) plus backend-specific .env overrides. The backend
itself never branches its behavior on `mode` beyond reporting it via
GET /system/mode -- its MQTT subscriber and REST API are identical
regardless of which mode produced the data.
"""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_PATH = _REPO_ROOT / "config.yaml"


def _load_yaml_config() -> dict:
    if not _CONFIG_PATH.exists():
        return {}
    with open(_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f) or {}


_yaml_config = _load_yaml_config()


class Settings:
    # Mode is read fresh on each access (not cached) so a running backend
    # picks up a mode change on next request without a restart being
    # strictly required for read-only reporting purposes.
    @property
    def mode(self) -> str:
        return _load_yaml_config().get("mode", "hardware")

    mqtt_broker_host: str = os.getenv("MQTT_BROKER_HOST", _yaml_config.get("mqtt", {}).get("broker_host", "localhost"))
    mqtt_broker_port: int = int(os.getenv("MQTT_BROKER_PORT", _yaml_config.get("mqtt", {}).get("broker_port", 1883)))

    database_path: str = os.getenv("DATABASE_PATH", _yaml_config.get("database", {}).get("path", "../database/yantrarakshak.db"))

    ollama_host: str = os.getenv("OLLAMA_HOST", _yaml_config.get("llm", {}).get("ollama_host", "http://localhost:11434"))
    ollama_model: str = os.getenv("OLLAMA_MODEL", _yaml_config.get("llm", {}).get("model", "llama3.1:8b"))

    backend_port: int = int(os.getenv("BACKEND_PORT", 8000))


settings = Settings()
