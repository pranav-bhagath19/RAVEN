"""
RAVEN Verification Database Repository
"""

from typing import Any
from sqlalchemy.orm import Session
from persistence.models import VerificationRecord


class VerificationRepository:
    """SQLAlchemy Repository for Verification outcomes."""

    def __init__(self, db: Session):
        self.db = db

    def save_verification(self, verification_data: dict[str, Any]) -> VerificationRecord:
        """Saves a VerificationRecord."""
        record = VerificationRecord(**verification_data)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def list_verifications(
        self,
        payment_id: str | None = None,
        recovery_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[VerificationRecord], int]:
        """Returns paginated Verification records."""
        query = self.db.query(VerificationRecord)
        if payment_id:
            query = query.filter(VerificationRecord.payment_id == payment_id)
        if recovery_type:
            query = query.filter(VerificationRecord.recovery_type == recovery_type)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(VerificationRecord.verified_at.desc()).offset(offset).limit(page_size).all()
        return items, total
