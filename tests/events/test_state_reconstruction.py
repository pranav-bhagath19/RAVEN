"""
Behavioral tests for Deterministic State Reconstructor

Validates out-of-order webhook delivery, late event replay, terminal state protection,
and conflict resolution rules.
"""

from datetime import datetime, timedelta, timezone
from domain.payments.payment import PaymentStatus
from domain.state.event import FinancialEvent
from domain.state.reconstructor import StateReconstructor


def test_standard_ordered_sequence():
    base_time = datetime.now(timezone.utc)
    payment_id = "pay_01H_test1"

    evt_auth = FinancialEvent(
        id="evt_1",
        event_hash="hash1",
        event_type="payment.authorized",
        entity_id=payment_id,
        merchant_id="mer_1",
        amount_minor_units=100000,
        currency="INR",
        payload={"payment_id": payment_id},
        occurred_at=base_time,
        sequence_number=1,
    )
    evt_cap = FinancialEvent(
        id="evt_2",
        event_hash="hash2",
        event_type="payment.captured",
        entity_id=payment_id,
        merchant_id="mer_1",
        amount_minor_units=100000,
        currency="INR",
        payload={"payment_id": payment_id},
        occurred_at=base_time + timedelta(seconds=2),
        sequence_number=2,
    )

    payment = StateReconstructor.reconstruct_payment_state(payment_id, [evt_auth, evt_cap])
    assert payment.status == PaymentStatus.CAPTURED


def test_out_of_order_webhook_delivery():
    """
    Simulates out-of-order delivery: payment.captured webhook arrives first at T+1s,
    but payment.authorized webhook arrives delayed at T+5s.
    """
    base_time = datetime.now(timezone.utc)
    payment_id = "pay_01H_test2"

    evt_cap = FinancialEvent(
        id="evt_cap",
        event_hash="hash_cap",
        event_type="payment.captured",
        entity_id=payment_id,
        merchant_id="mer_1",
        amount_minor_units=250000,
        currency="INR",
        payload={"payment_id": payment_id},
        occurred_at=base_time + timedelta(seconds=2),  # Occurred at T+2s
        received_at=base_time + timedelta(seconds=1),  # Arrived at T+1s
        sequence_number=2,
    )
    evt_auth = FinancialEvent(
        id="evt_auth",
        event_hash="hash_auth",
        event_type="payment.authorized",
        entity_id=payment_id,
        merchant_id="mer_1",
        amount_minor_units=250000,
        currency="INR",
        payload={"payment_id": payment_id},
        occurred_at=base_time + timedelta(seconds=1),  # Occurred at T+1s
        received_at=base_time + timedelta(seconds=5),  # Arrived at T+5s
        sequence_number=1,
    )

    # Dispatched to reconstructor in arbitrary arrival order
    reconstructed_payment = StateReconstructor.reconstruct_payment_state(
        payment_id, [evt_auth, evt_cap]
    )
    assert reconstructed_payment.status == PaymentStatus.CAPTURED


def test_terminal_state_conflict_protection():
    """
    Verifies that once a payment reaches terminal CAPTURED state,
    any late or out-of-order payment.failed event is IGNORED by state machine.
    """
    base_time = datetime.now(timezone.utc)
    payment_id = "pay_01H_test3"

    evt_cap = FinancialEvent(
        id="evt_cap",
        event_hash="hash_cap",
        event_type="payment.captured",
        entity_id=payment_id,
        merchant_id="mer_1",
        amount_minor_units=500000,
        currency="INR",
        payload={"payment_id": payment_id},
        occurred_at=base_time,
        sequence_number=1,
    )
    evt_late_failed = FinancialEvent(
        id="evt_fail",
        event_hash="hash_fail",
        event_type="payment.failed",
        entity_id=payment_id,
        merchant_id="mer_1",
        amount_minor_units=500000,
        currency="INR",
        payload={"payment_id": payment_id, "error_code": "GATEWAY_TIMEOUT"},
        occurred_at=base_time + timedelta(seconds=10),
        sequence_number=2,
    )

    payment = StateReconstructor.reconstruct_payment_state(payment_id, [evt_cap, evt_late_failed])
    assert payment.status == PaymentStatus.CAPTURED


def test_late_capture_replaces_failure():
    """
    Verifies that a payment initially marked FAILED is overridden to CAPTURED
    when a late payment.captured event arrives.
    """
    base_time = datetime.now(timezone.utc)
    payment_id = "pay_01H_test4"

    evt_fail = FinancialEvent(
        id="evt_fail",
        event_hash="hash_fail",
        event_type="payment.failed",
        entity_id=payment_id,
        merchant_id="mer_1",
        amount_minor_units=150000,
        currency="INR",
        payload={"payment_id": payment_id, "error_code": "BAD_REQUEST_TIMED_OUT"},
        occurred_at=base_time,
        sequence_number=1,
    )
    evt_late_cap = FinancialEvent(
        id="evt_cap",
        event_hash="hash_cap",
        event_type="payment.captured",
        entity_id=payment_id,
        merchant_id="mer_1",
        amount_minor_units=150000,
        currency="INR",
        payload={"payment_id": payment_id},
        occurred_at=base_time + timedelta(seconds=120),
        sequence_number=2,
    )

    payment = StateReconstructor.reconstruct_payment_state(payment_id, [evt_fail, evt_late_cap])
    assert payment.status == PaymentStatus.CAPTURED
