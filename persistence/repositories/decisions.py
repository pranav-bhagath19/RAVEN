"""
RAVEN DecisionTrace Database Repository

Firestore-backed repository implementation for DecisionTrace records.
"""

from typing import Any
from persistence.firestore_store import FirestoreDecisionRepository
from persistence.models import DecisionTraceRecord


class DecisionRepository:
    """Repository for DecisionTrace records backed by Firestore."""

    def __init__(self, db: Any = None) -> None:
        self._store = FirestoreDecisionRepository()

    def save_trace(self, trace_data: dict[str, Any]) -> DecisionTraceRecord:
        return self._store.save_trace(trace_data)

    def get_by_id(self, decision_id: str) -> DecisionTraceRecord | None:
        return self._store.get_by_id(decision_id)

    def get_latest_by_payment(self, payment_id: str) -> DecisionTraceRecord | None:
        return self._store.get_latest_by_payment(payment_id)

    def list_traces(
        self,
        status: str | None = None,
        payment_id: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[DecisionTraceRecord], int]:
        return self._store.list_traces(status=status, payment_id=payment_id, page=page, page_size=page_size)
