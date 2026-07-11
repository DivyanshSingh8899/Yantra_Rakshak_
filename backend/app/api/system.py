"""
System endpoints -- includes GET /system/mode, which is how the frontend's
Simulation Control Panel knows whether it should be active (Simulation
Mode) or read-only/informational (Hardware Mode), without the backend's
core data path caring about the distinction at all.
"""

import httpx
from fastapi import APIRouter

from app.config import settings

router = APIRouter(prefix="/api/v1/system", tags=["system"])


@router.get("/mode")
def get_mode():
    return {"mode": settings.mode}


@router.get("/health")
def get_health():
    llm_status = "unreachable"
    try:
        response = httpx.get(f"{settings.ollama_host}/api/tags", timeout=2.0)
        llm_status = "reachable" if response.status_code == 200 else "unreachable"
    except httpx.HTTPError:
        llm_status = "unreachable"

    return {
        "api": "ok",
        "mode": settings.mode,
        "llm": llm_status,
    }
