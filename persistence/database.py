"""
RAVEN Database Connection & Session Management

Provides SQLAlchemy engine, session maker, base ORM model, and schema initialization.
Supports PostgreSQL (production) and SQLite (in-memory / local fallback for demo/testing).
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Base ORM class for all RAVEN database entities."""

    pass


def get_database_url() -> str:
    """Returns database connection URL from environment variable or SQLite fallback."""
    return os.getenv("DATABASE_URL", "sqlite:///./raven_local.db")


def is_sqlite(url: str | None = None) -> bool:
    """Returns True if connection URL uses SQLite."""
    target_url = url or get_database_url()
    return target_url.startswith("sqlite")


_database_url = get_database_url()
_connect_args = {"check_same_thread": False} if is_sqlite(_database_url) else {}
engine = create_engine(_database_url, connect_args=_connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Creates all database tables defined in ORM models."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI / Application dependency yielding a database session context."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
