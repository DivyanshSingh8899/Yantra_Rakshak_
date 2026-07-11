"""
LLM Manager -- builds a prompt from an alert, calls the local Ollama
runtime, and persists the recommendation. Real Ollama HTTP call (not a
stub), with a deterministic fallback if Ollama is unreachable so the
pipeline never blocks on the LLM being down. Works identically for an
alert that originated from real hardware or from the simulator -- it only
ever sees the Alert/Machine rows, never the data source.

This is a deliberately minimal implementation of the fuller bilingual,
rubric-driven design documented earlier in the project -- the interface
(generate_recommendation) is stable, so that richer prompt/severity logic
can be layered in later without touching callers.
"""

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Alert, Machine, Recommendation

SYSTEM_PROMPT = """You are an industrial maintenance advisor supporting factory
technicians at small and medium manufacturing enterprises. You receive
anomaly data captured by vibration sensors on factory machinery, already
classified by an on-device AI model. Respond with a short, concrete
maintenance recommendation (2-4 sentences): what to check, the likely
cause, and how urgently to act. Do not use markdown formatting."""

FALLBACK_TEXT = (
    "Automated recommendation unavailable (local LLM unreachable). "
    "Manually inspect the machine for unusual vibration, noise, or heat, "
    "and compare current readings against its normal baseline."
)


class LLMManager:
    def __init__(self, db: Session):
        self.db = db

    def generate_recommendation(self, alert_id: int) -> Recommendation:
        alert = self.db.query(Alert).filter(Alert.alert_id == alert_id).first()
        if alert is None:
            raise ValueError(f"Alert {alert_id} not found")

        machine = self.db.query(Machine).filter(Machine.machine_id == alert.machine_id).first()
        machine_name = machine.name if machine else alert.machine_id

        user_prompt = (
            f"Machine: {machine_name}\n"
            f"Severity: {alert.severity}\n"
            f"Classification: {alert.classification or 'unclassified'}\n"
            f"Confidence: {alert.confidence}\n"
            f"Reconstruction error: {alert.reconstruction_error}\n"
        )

        text, status = self._call_ollama(user_prompt)

        recommendation = (
            self.db.query(Recommendation).filter(Recommendation.alert_id == alert_id).first()
        )
        if recommendation is None:
            recommendation = Recommendation(alert_id=alert_id)
            self.db.add(recommendation)

        recommendation.recommendation_text = text
        recommendation.model_used = settings.ollama_model if status == "success" else "fallback-template"
        recommendation.generation_status = status

        self.db.commit()
        self.db.refresh(recommendation)
        return recommendation

    def _call_ollama(self, user_prompt: str) -> tuple[str, str]:
        try:
            response = httpx.post(
                f"{settings.ollama_host}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "system": SYSTEM_PROMPT,
                    "prompt": user_prompt,
                    "stream": False,
                },
                timeout=15.0,
            )
            response.raise_for_status()
            text = response.json().get("response", "").strip()
            if not text:
                return FALLBACK_TEXT, "failed"
            return text, "success"
        except (httpx.HTTPError, httpx.TimeoutException, ValueError):
            return FALLBACK_TEXT, "failed"
