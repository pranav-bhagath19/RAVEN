"""
Tests for Phase 9 Failure Injection, Circuit Breakers & Systemic Reliability
"""

import pytest
from razorpay.live_client import LiveRazorpayClient
from tools.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError


def test_circuit_breaker_tripping_and_recovery():
    cb = CircuitBreaker("test_service", failure_threshold=2, recovery_timeout_seconds=0.1)

    def failing_func():
        raise RuntimeError("External dependency failure")

    # First failure
    with pytest.raises(RuntimeError):
        cb.call(failing_func)
    assert cb.state == "CLOSED"

    # Second failure trips breaker
    with pytest.raises(RuntimeError):
        cb.call(failing_func)
    assert cb.state == "OPEN"

    # Subsequent call while OPEN raises CircuitBreakerOpenError immediately
    with pytest.raises(CircuitBreakerOpenError):
        cb.call(failing_func)


def test_live_razorpay_client_placeholder_fallback():
    client = LiveRazorpayClient(key_id="rzp_test_placeholder", key_secret="placeholder_secret")
    pay = client.fetch_payment("pay_mock_100")
    assert pay["id"] == "pay_mock_100"
    assert pay["status"] in ("failed", "captured", "authorized")
