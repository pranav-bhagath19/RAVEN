"""
RAVEN Background Job Queue Database Repository
"""

from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session
from persistence.models import BackgroundJobRecord


class JobRepository:
    """SQLAlchemy Repository for background recovery jobs."""

    def __init__(self, db: Session):
        self.db = db

    def create_job(self, job_id: str, event_id: str, payment_id: str, payload: dict[str, Any]) -> BackgroundJobRecord:
        """Enqueues a new background recovery job in QUEUED status."""
        record = BackgroundJobRecord(
            job_id=job_id,
            event_id=event_id,
            payment_id=payment_id,
            status="QUEUED",
            attempt_count=0,
            max_attempts=3,
            payload_json=payload,
            next_attempt_at=datetime.now(timezone.utc),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def fetch_next_queued_job(self) -> BackgroundJobRecord | None:
        """Fetches next pending job ready for processing."""
        now = datetime.now(timezone.utc)
        job = (
            self.db.query(BackgroundJobRecord)
            .filter(
                BackgroundJobRecord.status.in_(["QUEUED", "RETRYING"]),
                BackgroundJobRecord.next_attempt_at <= now,
            )
            .order_by(BackgroundJobRecord.created_at.asc())
            .first()
        )
        if job:
            setattr(job, "status", "PROCESSING")
            current_attempts = getattr(job, "attempt_count", 0)
            setattr(job, "attempt_count", current_attempts + 1)
            setattr(job, "updated_at", now)
            self.db.commit()
            self.db.refresh(job)
        return job

    def mark_completed(self, job_id: str, trace_id: str | None = None) -> BackgroundJobRecord | None:
        """Marks job as COMPLETED."""
        job = self.db.query(BackgroundJobRecord).filter(BackgroundJobRecord.job_id == job_id).first()
        if job:
            setattr(job, "status", "COMPLETED")
            if trace_id:
                setattr(job, "trace_id", trace_id)
            setattr(job, "updated_at", datetime.now(timezone.utc))
            self.db.commit()
            self.db.refresh(job)
        return job

    def mark_failed(self, job_id: str, reason: str, can_retry: bool = True) -> BackgroundJobRecord | None:
        """Marks job as RETRYING or DEAD_LETTER upon failure."""
        job = self.db.query(BackgroundJobRecord).filter(BackgroundJobRecord.job_id == job_id).first()
        if job:
            setattr(job, "failure_reason", reason)
            current_attempts = getattr(job, "attempt_count", 1)
            max_att = getattr(job, "max_attempts", 3)
            if can_retry and current_attempts < max_att:
                setattr(job, "status", "RETRYING")
            else:
                setattr(job, "status", "DEAD_LETTER")
            setattr(job, "updated_at", datetime.now(timezone.utc))
            self.db.commit()
            self.db.refresh(job)
        return job
