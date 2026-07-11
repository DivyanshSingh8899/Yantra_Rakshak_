"""
SQLAlchemy ORM models for YantraRakshak's backend database.

Mirrors the ER diagram from the original backend architecture design
exactly (machines -> telemetry, machines -> alerts, alerts -> recommendation).
This schema is shared by both Hardware Mode and Simulation Mode -- neither
this file nor anything downstream of it needs to know which mode produced
a given row.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Machine(Base):
    __tablename__ = "machines"

    machine_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    location = Column(String)
    machine_type = Column(String)
    installed_at = Column(DateTime)
    status = Column(String, default="offline")  # "online" / "offline"
    last_seen_at = Column(DateTime)
    warning_threshold = Column(Float)
    critical_threshold = Column(Float)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    telemetry = relationship("Telemetry", back_populates="machine", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="machine", cascade="all, delete-orphan")


class Telemetry(Base):
    __tablename__ = "telemetry"

    telemetry_id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(String, ForeignKey("machines.machine_id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    vibration_rms = Column(Float)
    dominant_frequency = Column(Float)
    sound_level = Column(Float)
    reconstruction_error = Column(Float)
    raw_payload = Column(Text)  # original JSON string, for debugging/audit

    machine = relationship("Machine", back_populates="telemetry")


class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(String, ForeignKey("machines.machine_id"), nullable=False, index=True)
    triggered_at = Column(DateTime, nullable=False, index=True)
    severity = Column(String, nullable=False)  # "warning" / "critical"
    classification = Column(String)
    confidence = Column(Float)
    reconstruction_error = Column(Float)
    status = Column(String, default="new")  # "new" / "acknowledged" / "resolved"
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    machine = relationship("Machine", back_populates="alerts")
    recommendation = relationship(
        "Recommendation", back_populates="alert", uselist=False, cascade="all, delete-orphan"
    )


class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(Integer, ForeignKey("alerts.alert_id"), nullable=False, unique=True)
    generated_at = Column(DateTime, default=_utcnow)
    recommendation_text = Column(Text)
    model_used = Column(String)
    generation_status = Column(String, default="pending")  # "pending" / "success" / "failed"

    alert = relationship("Alert", back_populates="recommendation")
