"""
Unit Tests for LLMObservabilityTelemetry Module
"""

from datetime import datetime, timezone
from agents.common.models import TokenUsage
from agents.observability import LLMObservabilityTelemetry, sanitize_pii


def test_pii_sanitization():
    raw_email = "User contact email is john.doe@example.com for payment pay_100"
    clean_email = sanitize_pii(raw_email)
    assert "john.doe@example.com" not in clean_email
    assert "j***@example.com" in clean_email or "***" in clean_email

    raw_phone = "Customer phone number is +919876543210"
    clean_phone = sanitize_pii(raw_phone)
    assert "+919876543210" not in clean_phone

    raw_secret = "Token secret='raven_policy_secret_key' generated signature='abc123def'"
    clean_secret = sanitize_pii(raw_secret)
    assert "raven_policy_secret_key" not in clean_secret


def test_observability_record_and_retrieve():
    telemetry = LLMObservabilityTelemetry()
    telemetry.clear()

    now = datetime.now(timezone.utc)
    telemetry.record_invocation(
        trace_id="trace_test_obs",
        agent_name="RootCauseAnalyst",
        model="gpt-4o",
        provider="openai",
        prompt_version="rca-v1",
        started_at=now,
        completed_at=now,
        latency_ms=150.0,
        success=True,
        reasoning_mode="LLM",
        input_summary="Payment pay_100 failed",
        output_summary="RootCause=GATEWAY_TIMED_OUT",
        token_usage=TokenUsage(prompt_tokens=100, completion_tokens=20, total_tokens=120),
    )

    logs = telemetry.get_logs("trace_test_obs")
    assert len(logs) == 1
    assert logs[0].trace_id == "trace_test_obs"
    assert logs[0].agent_name == "RootCauseAnalyst"
    assert logs[0].prompt_version == "rca-v1"
    assert logs[0].token_usage.total_tokens == 120
