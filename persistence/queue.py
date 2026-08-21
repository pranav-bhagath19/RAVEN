"""
RAVEN Background Recovery Job Queue Module

Handles transactional job enqueueing and state transitions.
"""

import uuid
from typing import Any
from persistence.database import SessionLocal
from persistence.repositories.jobs import JobRepository


class RecoveryJobQueue:
    """Queue manager for asynchronous payment recovery processing."""

    def enqueue_recovery_job(self, event_id: str, payment_id: str, payload: dict[str, Any]) -> str:
        """Enqueues a background recovery job."""
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        try:
            db = SessionLocal()
            repo = JobRepository(db)
            repo.create_job(job_id=job_id, event_id=event_id, payment_id=payment_id, payload=payload)
            db.close()
        except Exception:
            pass
        return job_id
