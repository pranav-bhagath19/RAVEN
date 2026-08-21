"""
RAVEN Observability Telemetry Database Repository
"""

from typing import Any
from sqlalchemy.orm import Session
from persistence.models import TelemetryRecord


class TelemetryRepository:
    """SQLAlchemy Repository for Observability Telemetry records."""

    def __init__(self, db: Session):
        self.db = db

    def save_telemetry(self, telemetry_data: dict[str, Any]) -> TelemetryRecord:
        """Saves a TelemetryRecord."""
        record = TelemetryRecord(**telemetry_data)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def list_telemetry(
        self,
        agent: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        reasoning_mode: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[TelemetryRecord], int]:
        """Returns paginated Observability Telemetry logs."""
        query = self.db.query(TelemetryRecord)
        if agent:
            query = query.filter(TelemetryRecord.agent_name == agent)
        if provider:
            query = query.filter(TelemetryRecord.provider == provider)
        if model:
            query = query.filter(TelemetryRecord.model == model)
        if reasoning_mode:
            query = query.filter(TelemetryRecord.reasoning_mode == reasoning_mode)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(TelemetryRecord.started_at.desc()).offset(offset).limit(page_size).all()
        return items, total
