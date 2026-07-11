"""
SQLAlchemy engine/session setup. One SQLite file, shared by both Hardware
Mode and Simulation Mode -- the database has no concept of which mode
wrote a given row.
"""

import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base

DATABASE_PATH = os.getenv("DATABASE_PATH", "../database/yantrarakshak.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed for SQLite + FastAPI's threaded requests
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Creates all tables if they don't already exist. Safe to call on
    every startup -- idempotent."""
    os.makedirs(os.path.dirname(os.path.abspath(DATABASE_PATH)), exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency: yields a session, guarantees it's closed after
    the request, regardless of success or exception."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope():
    """Context-manager form for use outside FastAPI's request lifecycle
    (e.g. the MQTT subscriber's background thread)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
