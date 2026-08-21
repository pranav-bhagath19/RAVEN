"""
Tests for Phase 9 Concurrency & Race Condition Protection
"""

import concurrent.futures
import pytest
from persistence.database import SessionLocal, engine, init_db
from persistence.models import Base
from persistence.repositories.events import EventRepository


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    init_db()


def test_20_concurrent_duplicate_events():
    evt_data = {
        "event_id": "evt_concurrent_100",
        "event_hash": "hash_concurrent_unique_100",
        "event_type": "payment.failed",
        "entity_id": "pay_concurrent_100",
        "merchant_id": "mer_concurrent_100",
        "amount_minor": 100000,
        "currency": "INR",
        "occurred_at": "2026-08-22T00:00:00+00:00",
    }

    def save_worker():
        db = SessionLocal()
        try:
            repo = EventRepository(db)
            rec, is_new = repo.save_event(evt_data)
            return is_new
        finally:
            db.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(save_worker) for _ in range(20)]
        results = [f.result() for f in futures]

    # Exactly ONE thread should report is_new=True; all other threads report is_new=False
    new_count = sum(1 for r in results if r is True)
    assert new_count == 1
