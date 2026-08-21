"""
RAVEN Financial Event Database Repository
"""

from datetime import datetime, timezone
from typing import Any
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from persistence.models import FinancialEventRecord


class EventRepository:
    """SQLAlchemy Repository for Financial Events log."""

    def __init__(self, db: Session):
        self.db = db

    def save_event(self, event_data: dict[str, Any]) -> tuple[FinancialEventRecord, bool]:
        """
        Saves a financial event record transactionally.
        Returns (record, is_new). If event_hash exists, returns existing record with is_new=False.
        """
        data = dict(event_data)
        if isinstance(data.get("occurred_at"), str):
            data["occurred_at"] = datetime.fromisoformat(data["occurred_at"])
        elif not data.get("occurred_at"):
            data["occurred_at"] = datetime.now(timezone.utc)

        event_hash = data["event_hash"]
        existing = self.db.query(FinancialEventRecord).filter(FinancialEventRecord.event_hash == event_hash).first()
        if existing:
            return existing, False

        record = FinancialEventRecord(**data)
        try:
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            return record, True
        except IntegrityError:
            self.db.rollback()
            existing = self.db.query(FinancialEventRecord).filter(FinancialEventRecord.event_hash == event_hash).first()
            if existing:
                return existing, False
            raise

    def get_events_for_entity(self, entity_id: str) -> list[FinancialEventRecord]:
        """Returns ordered timeline events for a given entity_id (payment_id)."""
        return (
            self.db.query(FinancialEventRecord)
            .filter(FinancialEventRecord.entity_id == entity_id)
            .order_by(FinancialEventRecord.occurred_at.asc(), FinancialEventRecord.sequence_number.asc())
            .all()
        )

    def list_events(
        self,
        entity_id: str | None = None,
        event_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[FinancialEventRecord], int]:
        """Returns paginated financial event logs."""
        query = self.db.query(FinancialEventRecord)
        if entity_id:
            query = query.filter(FinancialEventRecord.entity_id == entity_id)
        if event_type:
            query = query.filter(FinancialEventRecord.event_type == event_type)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(FinancialEventRecord.received_at.desc()).offset(offset).limit(page_size).all()
        return items, total
