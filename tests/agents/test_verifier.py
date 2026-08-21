"""
Unit Tests for Deterministic Verification Agent
"""

from agents.verifier.models import VerificationResult
from agents.verifier.verifier import VerificationAgent
from domain.entities.payment import Payment, PaymentStatus
from domain.values.money import Money
from tools.base import ToolResult


def test_raven_attributed_recovery():
    verifier = VerificationAgent()

    payment_before = Payment(
        id="pay_ver_1",
        order_id="ord_1",
        merchant_id="mer_1",
        customer_id="cust_1",
        amount=Money(amount_minor=5000),
        status=PaymentStatus.FAILED,
    )
    payment_after = Payment(
        id="pay_ver_1",
        order_id="ord_1",
        merchant_id="mer_1",
        customer_id="cust_1",
        amount=Money(amount_minor=5000),
        status=PaymentStatus.CAPTURED,
    )
    exec_result = ToolResult(
        tool_name="smart_retry",
        action_id="act_ver_1",
        payment_id="pay_ver_1",
        status="SIMULATED_SUCCESS",
        payload={"message": "Retry executed"},
    )

    res = verifier.verify(
        payment_before=payment_before,
        payment_after=payment_after,
        execution_result=exec_result,
        action_id="act_ver_1",
    )

    assert isinstance(res, VerificationResult)
    assert res.is_recovered is True
    assert res.recovery_type == "RAVEN_ATTRIBUTED"
    assert res.recovered_amount.amount_minor == 5000


def test_pre_existing_recovery():
    verifier = VerificationAgent()

    payment_already_captured = Payment(
        id="pay_ver_2",
        order_id="ord_2",
        merchant_id="mer_1",
        customer_id="cust_1",
        amount=Money(amount_minor=5000),
        status=PaymentStatus.CAPTURED,
    )

    res = verifier.verify(
        payment_before=payment_already_captured,
        payment_after=payment_already_captured,
        action_id="act_ver_2",
    )

    assert res.is_recovered is True
    assert res.recovery_type == "PRE_EXISTING_RECOVERY"


def test_organic_customer_retry():
    verifier = VerificationAgent()

    payment_before = Payment(
        id="pay_ver_3",
        order_id="ord_3",
        merchant_id="mer_1",
        customer_id="cust_1",
        amount=Money(amount_minor=5000),
        status=PaymentStatus.FAILED,
    )
    payment_after = Payment(
        id="pay_ver_3",
        order_id="ord_3",
        merchant_id="mer_1",
        customer_id="cust_1",
        amount=Money(amount_minor=5000),
        status=PaymentStatus.CAPTURED,
    )

    # No RAVEN action execution result
    res = verifier.verify(
        payment_before=payment_before,
        payment_after=payment_after,
        execution_result=None,
    )

    assert res.is_recovered is True
    assert res.recovery_type == "ORGANIC_CUSTOMER_RETRY"


def test_no_recovery():
    verifier = VerificationAgent()

    payment_failed = Payment(
        id="pay_ver_4",
        order_id="ord_4",
        merchant_id="mer_1",
        customer_id="cust_1",
        amount=Money(amount_minor=5000),
        status=PaymentStatus.FAILED,
    )

    res = verifier.verify(
        payment_before=payment_failed,
        payment_after=payment_failed,
    )

    assert res.is_recovered is False
    assert res.recovery_type == "NO_RECOVERY"
    assert res.recovered_amount.amount_minor == 0
