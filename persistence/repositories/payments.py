"""
RAVEN Payment Entity Database Repository
"""

from typing import Any
from sqlalchemy.orm import Session
from persistence.models import PaymentRecord


class PaymentRepository:
    """SQLAlchemy Repository for Payment entities."""

    def __init__(self, db: Session):
        self.db = db

    def upsert_payment(self, payment_data: dict[str, Any]) -> PaymentRecord:
        """Upserts a payment record into database."""
        pid = payment_data["payment_id"]
        record = self.db.query(PaymentRecord).filter(PaymentRecord.payment_id == pid).first()
        if not record:
            record = PaymentRecord(**payment_data)
            self.db.add(record)
        else:
            for key, value in payment_data.items():
                if hasattr(record, key):
                    setattr(record, key, value)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_by_id(self, payment_id: str) -> PaymentRecord | None:
        """Finds payment record by ID."""
        return self.db.query(PaymentRecord).filter(PaymentRecord.payment_id == payment_id).first()

    def list_payments(
        self,
        status: str | None = None,
        merchant_id: str | None = None,
        customer_id: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[PaymentRecord], int]:
        """Returns paginated payment records matching filters."""
        query = self.db.query(PaymentRecord)
        if status:
            query = query.filter(PaymentRecord.status == status)
        if merchant_id:
            query = query.filter(PaymentRecord.merchant_id == merchant_id)
        if customer_id:
            query = query.filter(PaymentRecord.customer_id == customer_id)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(PaymentRecord.created_at.desc()).offset(offset).limit(page_size).all()
        return items, total
