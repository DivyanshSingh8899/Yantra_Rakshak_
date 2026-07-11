"""
Alert Manager -- owns the alert lifecycle (New -> Acknowledged -> Resolved).
Does not call the LLM or MQTT/WebSocket layers directly (kept loosely
coupled per the original design); the MQTT subscriber orchestrates calling
this, then the LLM manager, then broadcasting over WebSocket.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import Alert


class AlertManager:
    def __init__(self, db: Session):
        self.db = db

    def create_alert(
        self,
        machine_id: str,
        triggered_at: datetime,
        severity: str,
        classification: str | None = None,
        confidence: float | None = None,
        reconstruction_error: float | None = None,
    ) -> Alert:
        alert = Alert(
            machine_id=machine_id,
            triggered_at=triggered_at,
            severity=severity,
            classification=classification,
            confidence=confidence,
            reconstruction_error=reconstruction_error,
            status="new",
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def list_alerts(
        self,
        machine_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
    ) -> list[Alert]:
        query = self.db.query(Alert)
        if machine_id:
            query = query.filter(Alert.machine_id == machine_id)
        if status:
            query = query.filter(Alert.status == status)
        if severity:
            query = query.filter(Alert.severity == severity)
        return query.order_by(Alert.triggered_at.desc()).all()

    def get_active_alerts(self) -> list[Alert]:
        return self.db.query(Alert).filter(Alert.status != "resolved").order_by(Alert.triggered_at.desc()).all()

    def get_alert(self, alert_id: int) -> Alert | None:
        return self.db.query(Alert).filter(Alert.alert_id == alert_id).first()

    def acknowledge(self, alert_id: int) -> Alert | None:
        alert = self.get_alert(alert_id)
        if alert is None:
            return None
        alert.status = "acknowledged"
        alert.acknowledged_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def resolve(self, alert_id: int) -> Alert | None:
        alert = self.get_alert(alert_id)
        if alert is None:
            return None
        alert.status = "resolved"
        alert.resolved_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(alert)
        return alert
