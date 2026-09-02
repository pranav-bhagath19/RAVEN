"""
RAVEN Financial Event Database Repository

Firestore-backed repository implementation for Financial Events log.
"""

from typing import Any
from persistence.firestore_store import FirestoreEventRepository
from persistence.models import FinancialEventRecord


class EventRepository:
    """Repository for Financial Events log backed by Firestore."""

    def __init__(self, db: Any = None) -> None:
        self._store = FirestoreEventRepository()

    def save_event(self, event_data: dict[str, Any]) -> tuple[FinancialEventRecord, bool]:
        return self._store.save_event(event_data)

    def get_events_for_entity(self, entity_id: str) -> list[FinancialEventRecord]:
        return self._store.get_events_for_entity(entity_id)

    def list_events(
        self,
        entity_id: str | None = None,
        event_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[FinancialEventRecord], int]:
        return self._store.list_events(
            entity_id=entity_id,
            event_type=event_type,
            page=page,
            page_size=page_size,
        )
