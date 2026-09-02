"""
Tests for Phase 9 Database Persistence & Transactional Integrity
"""

import uuid
import pytest
from persistence.database import SessionLocal, engine, init_db
from persistence.models import Base
from persistence.repositories.events import EventRepository
from persistence.repositories.payments import PaymentRepository


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    init_db()


def test_payment_repository_upsert_and_retrieve():
    db = SessionLocal()
    repo = PaymentRepository(db)

    data = {
        "payment_id": f"pay_p9_{uuid.uuid4().hex[:8]}",
        "order_id": "order_p9_100",
        "merchant_id": "mer_p9_100",
        "customer_id": "cust_p9_100",
        "amount_minor": 500000,
        "currency": "INR",
        "status": "failed",
        "error_code": "GATEWAY_TIMED_OUT",
    }
    rec = repo.upsert_payment(data)
    assert rec.payment_id == data["payment_id"]

    fetched = repo.get_by_id(data["payment_id"])
    assert fetched is not None
    assert fetched.amount_minor == 500000

    items, total = repo.list_payments(merchant_id="mer_p9_100")
    assert total >= 1
    db.close()


def test_event_repository_transactional_deduplication():
    db = SessionLocal()
    repo = EventRepository(db)
    uid = uuid.uuid4().hex[:8]

    evt_data = {
        "event_id": f"evt_p9_{uid}",
        "event_hash": f"hash_canonical_p9_{uid}",
        "event_type": "payment.failed",
        "entity_id": f"pay_p9_dedup_{uid}",
        "merchant_id": "mer_p9_100",
        "amount_minor": 100000,
        "currency": "INR",
        "occurred_at": "2026-08-22T00:00:00+00:00",
    }
    rec1, is_new1 = repo.save_event(evt_data)
    assert is_new1 is True

    rec2, is_new2 = repo.save_event(evt_data)
    assert is_new2 is False
    assert rec2.event_id == rec1.event_id
    db.close()
