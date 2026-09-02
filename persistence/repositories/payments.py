"""
RAVEN Payment Entity Database Repository

Firestore-backed repository implementation for Payment entities.
"""

from typing import Any
from persistence.firestore_store import FirestorePaymentRepository
from persistence.models import PaymentRecord


class PaymentRepository:
    """Repository for Payment entities backed by Firestore."""

    def __init__(self, db: Any = None) -> None:
        self._store = FirestorePaymentRepository()

    def upsert_payment(self, payment_data: dict[str, Any]) -> PaymentRecord:
        return self._store.upsert_payment(payment_data)

    def get_by_id(self, payment_id: str) -> PaymentRecord | None:
        return self._store.get_by_id(payment_id)

    def list_payments(
        self,
        status: str | None = None,
        merchant_id: str | None = None,
        customer_id: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[PaymentRecord], int]:
        return self._store.list_payments(
            status=status,
            merchant_id=merchant_id,
            customer_id=customer_id,
            page=page,
            page_size=page_size,
        )
