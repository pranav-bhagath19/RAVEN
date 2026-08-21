"""
Unit tests for RAVEN Domain Entities
"""

import pytest
from pydantic import ValidationError
from domain.payments.customer import Customer
from domain.payments.merchant import Merchant, MerchantStatus
from domain.payments.order import Order
from domain.state.audit import ActorType, AuditEvent
from domain.state.decision_trace import DecisionTrace, DecisionTraceStatus
from domain.values.money import Money


def test_merchant_creation_and_currency_validation():
    merchant = Merchant(id="mer_01H123", name="Test Merchant Store", currency="inr")
    assert merchant.currency == "INR"
    assert merchant.status == MerchantStatus.ACTIVE

    with pytest.raises(ValidationError):
        Merchant(id="mer_01H123", name="Test Merchant Store", currency="INVALID")


def test_customer_creation_and_pii_masking():
    customer = Customer(
        id="cust_01H123",
        merchant_id="mer_01H123",
        email="pranav.sharma@example.com",
        phone="+919876543210",
        name="Pranav Sharma",
    )
    assert customer.masked_email() == "p***********a@example.com"
    assert customer.masked_phone() == "+91******3210"

    with pytest.raises(ValidationError):
        Customer(
            id="cust_01H123",
            merchant_id="mer_01H123",
            email="not-an-email",
            phone="123",
            name="Bad Customer",
        )


def test_order_balance_invariant_validation():
    m_500 = Money(500000, "INR")
    m_0 = Money(0, "INR")

    # Valid order: amount_paid (0) + amount_due (500000) == total amount (500000)
    order = Order(
        id="order_01H123",
        merchant_id="mer_01H123",
        customer_id="cust_01H123",
        amount=m_500,
        amount_paid=m_0,
        amount_due=m_500,
    )
    assert order.amount == m_500
    assert not order.is_fully_paid()

    # Invalid order balance invariant raises ValidationError
    with pytest.raises(ValidationError) as exc_info:
        Order(
            id="order_01H123",
            merchant_id="mer_01H123",
            customer_id="cust_01H123",
            amount=m_500,
            amount_paid=Money(1000, "INR"),
            amount_due=m_500,
        )
    assert "Order balance invariant violated" in str(exc_info.value)


def test_decision_trace_lifecycle_milestones():
    trace = DecisionTrace(
        decision_id="trace_01H123",
        recovery_opportunity_id="opp_01H123",
        merchant_id="mer_01H123",
        customer_id="cust_01H123",
        payment_id="pay_01H123",
    )
    assert trace.status == DecisionTraceStatus.INITIATED
    assert "created_at" in trace.timestamps

    trace.mark_milestone("analyzed_at")
    assert "analyzed_at" in trace.timestamps


def test_audit_event_creation():
    audit = AuditEvent(
        id="aud_01H123",
        trace_id="trace_01H123",
        entity_type="PAYMENT",
        entity_id="pay_01H123",
        actor_type=ActorType.SYSTEM,
        action="INGESTION",
        payload_snapshot={"status": "INGESTED"},
    )
    assert audit.actor_type == ActorType.SYSTEM
    assert audit.action == "INGESTION"
