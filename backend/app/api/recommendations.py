"""REST endpoints for LLM-generated maintenance recommendations."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Recommendation
from app.services.llm_manager import LLMManager

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.get("/{alert_id}")
def get_recommendation(alert_id: int, db: Session = Depends(get_db)):
    recommendation = db.query(Recommendation).filter(Recommendation.alert_id == alert_id).first()
    if recommendation is None:
        raise HTTPException(status_code=404, detail="No recommendation for this alert yet")
    return {
        "alert_id": alert_id,
        "recommendation_text": recommendation.recommendation_text,
        "model_used": recommendation.model_used,
        "generation_status": recommendation.generation_status,
        "generated_at": recommendation.generated_at.isoformat() if recommendation.generated_at else None,
    }


@router.post("/{alert_id}/regenerate", status_code=202)
def regenerate_recommendation(alert_id: int, db: Session = Depends(get_db)):
    recommendation = LLMManager(db).generate_recommendation(alert_id)
    return {
        "alert_id": alert_id,
        "recommendation_text": recommendation.recommendation_text,
        "generation_status": recommendation.generation_status,
    }
