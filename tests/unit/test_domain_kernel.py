"""
Comprehensive Unit Tests for RAVEN Deterministic Domain Kernel
"""

import pytest
from domain.entities.financial_event import FinancialEvent
from domain.entities.order import Order
from domain.entities.payment import Payment, PaymentStatus
from domain.entities.recovery import RecoveryAction, RecoveryOpportunity, RecoveryOutcome
from domain.enums import OpportunityStatus, RecoveryActionType, RecoveryOutcomeStatus
from domain.exceptions import (
    CurrencyMismatchError,
    InvalidIdentifierError,
    InvalidMoneyError,
    InvalidStateTransitionError,
)
from domain.values.identifiers import CustomerId, MerchantId, OrderId, PaymentId
from domain.values.money import Money


# ==========================================
# 1. Money Value Object Tests
# ==========================================

def test_money_minor_unit_preservation():
    m = Money(amount_minor=10000, currency="INR")
    assert m.amount_minor == 10000
    assert m.currency == "INR"
    assert m.to_dict() == {"amount_minor": 10000, "currency": "INR"}


def test_money_addition_and_subtraction():
    m1 = Money(amount_minor=500, currency="INR")
    m2 = Money(amount_minor=300, currency="INR")

    res_add = m1 + m2
    assert res_add.amount_minor == 800
    assert res_add.currency == "INR"

    res_sub = m1 - m2
    assert res_sub.amount_minor == 200
    assert res_sub.currency == "INR"


def test_money_currency_mismatch():
    inr_money = Money(amount_minor=100, currency="INR")
    usd_money = Money(amount_minor=100, currency="USD")

    with pytest.raises(CurrencyMismatchError):
        _ = inr_money + usd_money

    with pytest.raises(CurrencyMismatchError):
        _ = inr_money - usd_money

    with pytest.raises(CurrencyMismatchError):
        _ = inr_money < usd_money


def test_money_invalid_amount_or_currency():
    # Reject floating point values
    with pytest.raises(InvalidMoneyError):
        Money(amount_minor=10.5, currency="INR")  # type: ignore

    # Reject boolean values
    with pytest.raises(InvalidMoneyError):
        Money(amount_minor=True, currency="INR")  # type: ignore

    # Reject invalid currency
    with pytest.raises(InvalidMoneyError):
        Money(amount_minor=100, currency="INVALID_CURRENCY")


def test_money_comparisons():
    m1 = Money(amount_minor=100, currency="INR")
    m2 = Money(amount_minor=200, currency="INR")
    m3 = Money(amount_minor=100, currency="INR")

    assert m1 < m2
    assert m2 > m1
    assert m1 <= m3
    assert m1 == m3


# ==========================================
# 2. Identifiers Tests
# ==========================================

def test_identifiers_validation_and_equality():
    mer_id = MerchantId("mer_01H123")
    assert str(mer_id) == "mer_01H123"

    cust_id = CustomerId("cust_01H123")
    assert str(cust_id) == "cust_01H123"

    order_id = OrderId("order_01H123")
    assert str(order_id) == "order_01H123"

    pay_id = PaymentId("pay_01H123")
    assert str(pay_id) == "pay_01H123"

    with pytest.raises(InvalidIdentifierError):
        MerchantId("")


# ==========================================
# 3. Payment Domain State Machine Tests
# ==========================================

def test_payment_valid_state_transitions():
    pay = Payment(
        id="pay_01H123",
        order_id="order_01H123",
        merchant_id="mer_01H123",
        customer_id="cust_01H123",
        amount=Money(amount_minor=50000, currency="INR"),
        status=PaymentStatus.CREATED,
    )
    assert pay.status == PaymentStatus.CREATED

    pay.transition_to(PaymentStatus.AUTHORIZED)
    assert pay.status == PaymentStatus.AUTHORIZED

    pay.transition_to(PaymentStatus.CAPTURED)
    assert pay.status == PaymentStatus.CAPTURED
    assert pay.is_terminal_success()


def test_payment_invalid_state_transition_raises_exception():
    pay = Payment(
        id="pay_01H123",
        order_id="order_01H123",
        merchant_id="mer_01H123",
        customer_id="cust_01H123",
        amount=Money(amount_minor=50000, currency="INR"),
        status=PaymentStatus.CAPTURED,
    )

    # Transitioning from CAPTURED to AUTHORIZED is illegal!
    with pytest.raises(InvalidStateTransitionError) as exc_info:
        pay.transition_to(PaymentStatus.AUTHORIZED)

    assert "Cannot transition payment" in str(exc_info.value)
    # Confirm state preserved unmutated!
    assert pay.status == PaymentStatus.CAPTURED


# ==========================================
# 4. FinancialEvent Hashing Stability Tests
# ==========================================

def test_canonical_hash_stability():
    payload_1 = {"b": 2, "a": 1, "nested": {"y": 2, "x": 1}}
    payload_2 = {"a": 1, "b": 2, "nested": {"x": 1, "y": 2}}

    hash_1 = FinancialEvent.compute_canonical_hash(payload_1)
    hash_2 = FinancialEvent.compute_canonical_hash(payload_2)

    assert hash_1 == hash_2
    assert len(hash_1) == 64  # Valid SHA-256 hex string length


# ==========================================
# 5. Order Balance Invariants with Money
# ==========================================

def test_order_construction_and_money_invariants():
    order = Order.create(
        order_id="order_01H123",
        merchant_id="mer_01H123",
        customer_id="cust_01H123",
        amount_minor=100000,
        currency="INR",
    )
    assert order.amount == Money(100000, "INR")
    assert order.amount_paid == Money(0, "INR")
    assert order.amount_due == Money(100000, "INR")
    assert not order.is_fully_paid()


# ==========================================
# 6. Recovery Domain Entities Tests
# ==========================================

def test_recovery_opportunity_action_and_outcome():
    risk_money = Money(50000, "INR")
    opp = RecoveryOpportunity(
        id="opp_01H123",
        merchant_id="mer_01H123",
        payment_id="pay_01H123",
        amount_at_risk=risk_money,
        risk_category="TRANSIENT_GATEWAY_TIMEOUT",
        status=OpportunityStatus.OPEN,
    )
    assert opp.amount_at_risk == risk_money

    act = RecoveryAction(
        id="act_01H123",
        opportunity_id="opp_01H123",
        action_type=RecoveryActionType.SMART_RETRY,
        expected_recovery_value=risk_money,
        agent_confidence=0.85,
    )
    assert act.expected_recovery_value == risk_money
    assert act.agent_confidence == 0.85

    outcome = RecoveryOutcome(
        id="out_01H123",
        opportunity_id="opp_01H123",
        action_id="act_01H123",
        status=RecoveryOutcomeStatus.RECOVERED,
        is_recovered=True,
        recovered_amount=risk_money,
    )
    assert outcome.is_recovered is True
    assert outcome.recovered_amount == risk_money
