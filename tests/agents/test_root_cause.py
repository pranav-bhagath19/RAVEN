"""
Unit and Fallback Tests for Root Cause Analyst Agent
"""

import pytest
from agents.common.provider import MockLLMProvider
from agents.root_cause.analyst import RootCauseAnalyst
from agents.root_cause.fallback import evaluate_deterministic_root_cause_fallback
from agents.root_cause.models import RootCauseAnalysis
from domain.entities.payment import Payment, PaymentStatus
from domain.values.money import Money


def test_valid_structured_llm_output():
    analyst = RootCauseAnalyst()

    def mock_generator(prompt, model):
        return RootCauseAnalysis(
            payment_id="pay_test_100",
            root_cause="GATEWAY_TIMED_OUT",
            explanation="Timeout during gateway authorization.",
            evidence=["ev_1"],
            recoverability="HIGH",
            confidence=0.90,
            contributing_factors=["Bank congestion"],
            recommended_direction="Smart retry",
            reasoning_mode="LLM",
        )

    provider = MockLLMProvider(mock_response_generator=mock_generator)
    payment = Payment(
        id="pay_test_100",
        order_id="ord_1",
        merchant_id="mer_1",
        customer_id="cust_1",
        amount=Money(amount_minor=1000),
        status=PaymentStatus.FAILED,
    )

    rca = analyst.analyze(payment=payment, provider=provider)

    assert rca.root_cause == "GATEWAY_TIMED_OUT"
    assert rca.confidence == 0.90
    assert rca.recoverability == "HIGH"
    assert rca.reasoning_mode == "LLM"


def test_confidence_bounds_validation():
    with pytest.raises(ValueError):
        RootCauseAnalysis(
            payment_id="pay_test",
            root_cause="TIMED_OUT",
            explanation="Test",
            recoverability="HIGH",
            confidence=1.5,  # Invalid: > 1.0
            recommended_direction="Test",
        )


def test_provider_timeout_fallback():
    analyst = RootCauseAnalyst()
    provider = MockLLMProvider(force_timeout=True)
    payment = Payment(
        id="pay_timeout_1",
        order_id="ord_1",
        merchant_id="mer_1",
        customer_id="cust_1",
        amount=Money(amount_minor=1000),
        status=PaymentStatus.FAILED,
    )

    rca = analyst.analyze(payment=payment, provider=provider, error_code="GATEWAY_TIMED_OUT")

    assert rca.root_cause == "GATEWAY_TIMED_OUT"
    assert rca.reasoning_mode == "DETERMINISTIC_FALLBACK"


def test_provider_failure_fallback():
    analyst = RootCauseAnalyst()
    provider = MockLLMProvider(force_failure=True)
    payment = Payment(
        id="pay_fail_1",
        order_id="ord_1",
        merchant_id="mer_1",
        customer_id="cust_1",
        amount=Money(amount_minor=1000),
        status=PaymentStatus.FAILED,
    )

    rca = analyst.analyze(
        payment=payment,
        provider=provider,
        error_code="BAD_REQUEST_PAYMENT_DECLINED_INSUFFICIENT_FUNDS",
    )

    assert rca.root_cause == "INSUFFICIENT_FUNDS"
    assert rca.reasoning_mode == "DETERMINISTIC_FALLBACK"


def test_deterministic_fallback_heuristics():
    rca_timeout = evaluate_deterministic_root_cause_fallback(None, error_code="GATEWAY_TIMED_OUT")
    assert rca_timeout.root_cause == "GATEWAY_TIMED_OUT"

    rca_funds = evaluate_deterministic_root_cause_fallback(None, error_code="INSUFFICIENT_FUNDS")
    assert rca_funds.root_cause == "INSUFFICIENT_FUNDS"

    rca_token = evaluate_deterministic_root_cause_fallback(None, error_code="RECURRING_TOKEN_EXPIRED")
    assert rca_token.root_cause == "RECURRING_TOKEN_EXPIRED"

    rca_3ds = evaluate_deterministic_root_cause_fallback(None, error_code="AUTHENTICATION_ABANDONED")
    assert rca_3ds.root_cause == "AUTHENTICATION_ABANDONED"
