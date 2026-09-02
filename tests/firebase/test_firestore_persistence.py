"""
Unit Tests for RAVEN Firestore Persistence & Repository Layer
"""

import uuid
import pytest
from persistence.firebase import reset_firestore_emulator
from persistence.firestore_store import (
    FirestoreDecisionRepository,
    FirestoreEventRepository,
    FirestorePaymentRepository,
)


@pytest.fixture(autouse=True)
def setup_firestore():
    reset_firestore_emulator()


def test_firestore_payment_repository_crud():
    repo = FirestorePaymentRepository()
    uid = uuid.uuid4().hex[:8]

    data = {
        "payment_id": f"pay_fs_{uid}",
        "order_id": f"order_fs_{uid}",
        "tenant_id": f"tenant_{uid}",
        "merchant_id": f"mer_{uid}",
        "customer_id": f"cust_{uid}",
        "amount_minor": 250000,
        "currency": "INR",
        "status": "failed",
        "error_code": "BAD_REQUEST",
    }
    rec = repo.upsert_payment(data)
    assert rec.payment_id == data["payment_id"]
    assert rec.tenant_id == data["tenant_id"]

    fetched = repo.get_by_id(data["payment_id"])
    assert fetched is not None
    assert fetched.amount_minor == 250000
    assert fetched.merchant_id == data["merchant_id"]

    items, total = repo.list_payments(merchant_id=data["merchant_id"])
    assert total == 1
    assert items[0].payment_id == data["payment_id"]


def test_firestore_event_repository_deduplication():
    repo = FirestoreEventRepository()
    uid = uuid.uuid4().hex[:8]

    evt_data = {
        "event_id": f"evt_fs_{uid}",
        "tenant_id": f"tenant_{uid}",
        "event_hash": f"hash_fs_canonical_{uid}",
        "event_type": "payment.failed",
        "entity_id": f"pay_fs_{uid}",
        "merchant_id": f"mer_{uid}",
        "amount_minor": 250000,
        "currency": "INR",
        "occurred_at": "2026-09-01T20:00:00+00:00",
    }

    rec1, is_new1 = repo.save_event(evt_data)
    assert is_new1 is True
    assert rec1.event_id == evt_data["event_id"]

    rec2, is_new2 = repo.save_event(evt_data)
    assert is_new2 is False
    assert rec2.event_id == rec1.event_id

    events = repo.get_events_for_entity(evt_data["entity_id"])
    assert len(events) == 1
    assert events[0].event_hash == evt_data["event_hash"]


def test_firestore_decision_trace_repository():
    repo = FirestoreDecisionRepository()

    trace_data = {
        "decision_id": "dec_fs_100",
        "tenant_id": "tenant_alpha",
        "policy_id": "pol_fs_100",
        "opportunity_id": "opp_fs_100",
        "merchant_id": "mer_alpha",
        "customer_id": "cust_alpha",
        "payment_id": "pay_fs_100",
        "status": "EXECUTED",
        "root_cause": "CARD_EXPIRED",
        "selected_action_type": "RETRY_SUBMIT",
    }

    rec = repo.save_trace(trace_data)
    assert rec.decision_id == "dec_fs_100"

    latest = repo.get_latest_by_payment("pay_fs_100")
    assert latest is not None
    assert latest.decision_id == "dec_fs_100"
    assert latest.selected_action_type == "RETRY_SUBMIT"
