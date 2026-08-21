"""
RAVEN DecisionTrace Database Repository
"""

from typing import Any
from sqlalchemy.orm import Session
from persistence.models import DecisionTraceRecord


class DecisionRepository:
    """SQLAlchemy Repository for DecisionTrace records."""

    def __init__(self, db: Session):
        self.db = db

    def save_trace(self, trace_data: dict[str, Any]) -> DecisionTraceRecord:
        """Upserts a DecisionTrace record into database."""
        did = trace_data["decision_id"]
        record = self.db.query(DecisionTraceRecord).filter(DecisionTraceRecord.decision_id == did).first()
        if not record:
            record = DecisionTraceRecord(**trace_data)
            self.db.add(record)
        else:
            for key, value in trace_data.items():
                if hasattr(record, key):
                    setattr(record, key, value)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_by_id(self, decision_id: str) -> DecisionTraceRecord | None:
        """Finds DecisionTrace record by ID."""
        return self.db.query(DecisionTraceRecord).filter(DecisionTraceRecord.decision_id == decision_id).first()

    def get_latest_by_payment(self, payment_id: str) -> DecisionTraceRecord | None:
        """Finds latest DecisionTrace record for a payment."""
        return (
            self.db.query(DecisionTraceRecord)
            .filter(DecisionTraceRecord.payment_id == payment_id)
            .order_by(DecisionTraceRecord.created_at.desc())
            .first()
        )

    def list_traces(
        self,
        status: str | None = None,
        payment_id: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[DecisionTraceRecord], int]:
        """Returns paginated DecisionTrace records."""
        query = self.db.query(DecisionTraceRecord)
        if status:
            query = query.filter(DecisionTraceRecord.status == status)
        if payment_id:
            query = query.filter(DecisionTraceRecord.payment_id == payment_id)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(DecisionTraceRecord.created_at.desc()).offset(offset).limit(page_size).all()
        return items, total
