"""
Tests for Phase 9 Background Worker & Async Queue Processing
"""

import pytest
from apps.worker.worker import RecoveryWorker
from events.ingestion import EventIngestionService
from persistence.database import init_db
from persistence.queue import RecoveryJobQueue


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_enqueue_and_process_background_job():
    ingestion = EventIngestionService()
    queue = RecoveryJobQueue()
    worker = RecoveryWorker()

    evt_payload = {
        "payment_id": "pay_worker_100",
        "merchant_id": "mer_worker_100",
        "customer_id": "cust_worker_100",
        "amount": 250000,
        "currency": "INR",
        "error_code": "GATEWAY_TIMED_OUT",
        "error_description": "Gateway timed out",
    }
    evt = ingestion.ingest_event(raw_payload=evt_payload, event_type="payment.failed")

    job_id = queue.enqueue_recovery_job(
        event_id=evt.id,
        payment_id=evt.entity_id,
        payload=evt_payload,
    )
    assert job_id.startswith("job_")

    res = worker.process_one_job()
    assert res is not None
    assert res["status"] == "COMPLETED"
    assert "trace_id" in res
