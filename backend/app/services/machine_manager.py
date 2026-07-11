"""
Machine Manager -- owns the machine registry and each machine's derived
health state. Used identically regardless of whether telemetry originated
from real Arduino UNO Q hardware or the Simulation Mode publisher.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import Machine


class MachineManager:
    def __init__(self, db: Session):
        self.db = db

    def list_machines(self) -> list[Machine]:
        return self.db.query(Machine).all()

    def get_machine(self, machine_id: str) -> Machine | None:
        return self.db.query(Machine).filter(Machine.machine_id == machine_id).first()

    def register_machine(
        self,
        machine_id: str,
        name: str,
        location: str | None = None,
        machine_type: str | None = None,
        warning_threshold: float | None = None,
        critical_threshold: float | None = None,
    ) -> Machine:
        machine = self.get_machine(machine_id)
        if machine is not None:
            return machine

        machine = Machine(
            machine_id=machine_id,
            name=name,
            location=location,
            machine_type=machine_type,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            status="offline",
        )
        self.db.add(machine)
        self.db.commit()
        self.db.refresh(machine)
        return machine

    def ensure_machine_exists(self, machine_id: str) -> Machine:
        """Called by the MQTT subscriber the first time a machine_id is
        seen -- auto-registers it with sensible defaults so telemetry/alert
        ingestion never fails just because a machine wasn't manually
        pre-registered through the API first. Works the same for a
        simulated machine_id as a real one."""
        machine = self.get_machine(machine_id)
        if machine is not None:
            return machine
        return self.register_machine(machine_id=machine_id, name=machine_id)

    def update_status(self, machine_id: str, status: str) -> None:
        machine = self.ensure_machine_exists(machine_id)
        machine.status = status
        machine.last_seen_at = datetime.now(timezone.utc)
        self.db.commit()

    def touch_last_seen(self, machine_id: str) -> None:
        machine = self.ensure_machine_exists(machine_id)
        machine.last_seen_at = datetime.now(timezone.utc)
        if machine.status != "online":
            machine.status = "online"
        self.db.commit()

    def health_summary(self, machine_id: str) -> dict:
        from app.db.models import Alert

        machine = self.get_machine(machine_id)
        if machine is None:
            return {"status": "unknown", "active_alert_count": 0}

        active_alerts = (
            self.db.query(Alert)
            .filter(Alert.machine_id == machine_id, Alert.status != "resolved")
            .all()
        )
        if any(a.severity == "critical" for a in active_alerts):
            status = "critical"
        elif any(a.severity == "warning" for a in active_alerts):
            status = "warning"
        else:
            status = "healthy"

        return {"status": status, "active_alert_count": len(active_alerts)}
