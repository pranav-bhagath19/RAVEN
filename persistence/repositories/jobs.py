"""
RAVEN Background Job Queue Database Repository

Firestore-backed repository implementation for background recovery jobs.
"""

from typing import Any
from persistence.firestore_store import FirestoreJobRepository
from persistence.models import BackgroundJobRecord


class JobRepository:
    """Repository for background recovery jobs backed by Firestore."""

    def __init__(self, db: Any = None) -> None:
        self._store = FirestoreJobRepository()

    def create_job(self, job_id: str, event_id: str, payment_id: str, payload: dict[str, Any]) -> BackgroundJobRecord:
        return self._store.create_job(job_id=job_id, event_id=event_id, payment_id=payment_id, payload=payload)

    def fetch_next_queued_job(self) -> BackgroundJobRecord | None:
        return self._store.fetch_next_queued_job()

    def mark_completed(self, job_id: str, trace_id: str | None = None) -> BackgroundJobRecord | None:
        return self._store.mark_completed(job_id=job_id, trace_id=trace_id)

    def mark_failed(self, job_id: str, reason: str, can_retry: bool = True) -> BackgroundJobRecord | None:
        return self._store.mark_failed(job_id=job_id, reason=reason, can_retry=can_retry)
