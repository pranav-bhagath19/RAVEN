"""
RAVEN Production Background Recovery Worker

Processes queued recovery jobs asynchronously outside the HTTP request lifecycle.
"""

import time
from typing import Any
from agents.orchestrator import AgentOrchestrator
from domain.entities.customer import Customer
from domain.entities.merchant import Merchant
from domain.enums import MerchantStatus
from events.ingestion import EventIngestionService
from persistence.database import SessionLocal
from persistence.repositories.jobs import JobRepository


class RecoveryWorker:
    """Background worker daemon processing queued payment recovery jobs."""

    def __init__(self, orchestrator: AgentOrchestrator | None = None) -> None:
        self.orchestrator = orchestrator or AgentOrchestrator()
        self.ingestion = EventIngestionService()

    def process_one_job(self) -> dict[str, Any] | None:
        """Fetches and executes a single queued recovery job. Returns job summary if processed."""
        db = SessionLocal()
        job_repo = JobRepository(db)
        job = job_repo.fetch_next_queued_job()

        if not job:
            db.close()
            return None

        try:
            payload: dict[str, Any] = getattr(job, "payload_json", {}) or {}
            job_id = str(getattr(job, "job_id", ""))
            payment_id = str(getattr(job, "payment_id", ""))
            merchant_id = str(payload.get("merchant_id", "mer_default"))
            customer_id = str(payload.get("customer_id", "cust_default"))
            error_code = str(payload.get("error_code", "GATEWAY_TIMED_OUT"))

            events = self.ingestion.get_events_for_entity(payment_id)
            merchant = Merchant(id=merchant_id, name="Merchant Store", currency="INR", status=MerchantStatus.ACTIVE)
            customer = Customer(id=customer_id, merchant_id=merchant_id, email="customer@example.com", phone="+919876543210", name="Valued Customer")

            trace = self.orchestrator.process_payment_failure(
                events=events,
                merchant=merchant,
                customer=customer,
                error_code=error_code,
            )

            job_repo.mark_completed(job_id, trace_id=trace.decision_id)
            db.close()
            return {"job_id": job_id, "status": "COMPLETED", "trace_id": trace.decision_id}

        except Exception as exc:
            job_id_fail = str(getattr(job, "job_id", ""))
            job_repo.mark_failed(job_id_fail, reason=str(exc))
            db.close()
            return {"job_id": job_id_fail, "status": "FAILED", "error": str(exc)}

    def run_loop(self, poll_interval_seconds: float = 1.0, max_jobs: int | None = None) -> int:
        """Runs continuous polling loop until stopped or max_jobs processed."""
        processed_count = 0
        while True:
            res = self.process_one_job()
            if res:
                processed_count += 1
                if max_jobs and processed_count >= max_jobs:
                    break
            else:
                time.sleep(poll_interval_seconds)
        return processed_count
