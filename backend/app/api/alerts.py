"""REST endpoints for alert history/lifecycle."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.alert_manager import AlertManager

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


def _serialize(alert):
    return {
        "alert_id": alert.alert_id,
        "machine_id": alert.machine_id,
        "triggered_at": alert.triggered_at.isoformat(),
        "severity": alert.severity,
        "classification": alert.classification,
        "confidence": alert.confidence,
        "reconstruction_error": alert.reconstruction_error,
        "status": alert.status,
    }


@router.get("")
def list_alerts(
    machine_id: str | None = None,
    status: str | None = None,
    severity: str | None = None,
    db: Session = Depends(get_db),
):
    alerts = AlertManager(db).list_alerts(machine_id=machine_id, status=status, severity=severity)
    return [_serialize(a) for a in alerts]


@router.get("/active")
def get_active_alerts(db: Session = Depends(get_db)):
    return [_serialize(a) for a in AlertManager(db).get_active_alerts()]


@router.get("/{alert_id}")
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = AlertManager(db).get_alert(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    payload = _serialize(alert)
    if alert.recommendation is not None:
        payload["recommendation"] = {
            "recommendation_text": alert.recommendation.recommendation_text,
            "model_used": alert.recommendation.model_used,
            "generation_status": alert.recommendation.generation_status,
        }
    else:
        payload["recommendation"] = None
    return payload


@router.post("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = AlertManager(db).acknowledge(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return _serialize(alert)


@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = AlertManager(db).resolve(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return _serialize(alert)
