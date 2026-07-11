"""
REST endpoints for machine registry + health summary. Identical behavior
regardless of whether a machine's data originates from real hardware or
the simulator -- this router only ever talks to MachineManager/HistoryManager.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.history_manager import HistoryManager
from app.services.machine_manager import MachineManager

router = APIRouter(prefix="/api/v1/machines", tags=["machines"])


class MachineCreateRequest(BaseModel):
    machine_id: str
    name: str
    location: str | None = None
    machine_type: str | None = None
    warning_threshold: float | None = None
    critical_threshold: float | None = None


@router.get("")
def list_machines(db: Session = Depends(get_db)):
    manager = MachineManager(db)
    machines = manager.list_machines()
    return [
        {
            "machine_id": m.machine_id,
            "name": m.name,
            "location": m.location,
            "machine_type": m.machine_type,
            "status": m.status,
            "last_seen_at": m.last_seen_at.isoformat() if m.last_seen_at else None,
            "health": manager.health_summary(m.machine_id)["status"],
        }
        for m in machines
    ]


@router.post("", status_code=201)
def register_machine(request: MachineCreateRequest, db: Session = Depends(get_db)):
    machine = MachineManager(db).register_machine(**request.model_dump())
    return {"machine_id": machine.machine_id, "name": machine.name}


@router.get("/{machine_id}")
def get_machine(machine_id: str, db: Session = Depends(get_db)):
    manager = MachineManager(db)
    machine = manager.get_machine(machine_id)
    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return {
        "machine_id": machine.machine_id,
        "name": machine.name,
        "location": machine.location,
        "machine_type": machine.machine_type,
        "installed_at": machine.installed_at.isoformat() if machine.installed_at else None,
        "status": machine.status,
        "health": manager.health_summary(machine_id),
    }


@router.get("/{machine_id}/telemetry")
def get_machine_telemetry(
    machine_id: str,
    start: datetime | None = None,
    end: datetime | None = None,
    db: Session = Depends(get_db),
):
    start = start or datetime(1970, 1, 1)
    end = end or datetime.utcnow()
    records = HistoryManager(db).get_range(machine_id, start, end)
    return [
        {
            "timestamp": r.timestamp.isoformat(),
            "reconstruction_error": r.reconstruction_error,
        }
        for r in records
    ]


@router.get("/{machine_id}/health")
def get_machine_health(machine_id: str, db: Session = Depends(get_db)):
    return MachineManager(db).health_summary(machine_id)
