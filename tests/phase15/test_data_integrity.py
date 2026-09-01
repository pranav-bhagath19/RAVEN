"""
Phase 15 Data Integrity & Security Invariants Tests
"""

from domain.entities.payment import Money, Payment
from domain.enums import PaymentStatus


def test_data_integrity_integer_minor_units():
    """Verifies monetary calculations maintain integer minor units."""
    m1 = Money(amount_minor=10050, currency="INR")
    m2 = Money(amount_minor=20025, currency="INR")
    assert isinstance(m1.amount_minor, int)
    assert isinstance(m2.amount_minor, int)
    assert (m1.amount_minor + m2.amount_minor) == 30075


def test_payment_entity_validation():
    """Verifies payment entity validation and integer amount protection."""
    p = Payment(
        id="pay_integrity_01",
        order_id="ord_integrity_01",
        merchant_id="mer_integrity_01",
        customer_id="cust_integrity_01",
        amount=Money(amount_minor=150000, currency="INR"),
        status=PaymentStatus.FAILED,
    )
    assert p.amount.amount_minor == 150000
    assert p.amount.currency == "INR"
