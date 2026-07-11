"""
History Manager -- stores and queries telemetry time-series. Identical
code path for hardware-sourced and simulator-sourced telemetry.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import Telemetry


class HistoryManager:
    def __init__(self, db: Session):
        self.db = db

    def store_telemetry(
        self,
        machine_id: str,
        timestamp: datetime,
        vibration_rms: float | None = None,
        dominant_frequency: float | None = None,
        sound_level: float | None = None,
        reconstruction_error: float | None = None,
        raw_payload: str | None = None,
    ) -> Telemetry:
        record = Telemetry(
            machine_id=machine_id,
            timestamp=timestamp,
            vibration_rms=vibration_rms,
            dominant_frequency=dominant_frequency,
            sound_level=sound_level,
            reconstruction_error=reconstruction_error,
            raw_payload=raw_payload,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_range(self, machine_id: str, start: datetime, end: datetime) -> list[Telemetry]:
        return (
            self.db.query(Telemetry)
            .filter(
                Telemetry.machine_id == machine_id,
                Telemetry.timestamp >= start,
                Telemetry.timestamp <= end,
            )
            .order_by(Telemetry.timestamp.asc())
            .all()
        )

    def get_latest(self, machine_id: str) -> Telemetry | None:
        return (
            self.db.query(Telemetry)
            .filter(Telemetry.machine_id == machine_id)
            .order_by(Telemetry.timestamp.desc())
            .first()
        )
