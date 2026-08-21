"""
Unit Tests for BaseLLMProvider and MockLLMProvider
"""

import pytest
from agents.common.errors import LLMProviderError, LLMTimeoutError, LLMValidationError
from agents.common.models import LLMResponse
from agents.common.provider import MockLLMProvider
from agents.root_cause.models import RootCauseAnalysis


def test_mock_provider_structured_output():
    def mock_gen(prompt, response_model):
        return RootCauseAnalysis(
            payment_id="pay_prov_1",
            root_cause="INSUFFICIENT_FUNDS",
            explanation="Insufficient balance.",
            recoverability="MEDIUM",
            confidence=0.85,
            recommended_direction="Payment link",
        )

    provider = MockLLMProvider(mock_response_generator=mock_gen)

    res_obj, res_wrapper = provider.generate_structured(
        prompt="Analyze failure",
        system_prompt="System instructions",
        response_model=RootCauseAnalysis,
        prompt_version="rca-v1",
    )

    assert isinstance(res_obj, RootCauseAnalysis)
    assert isinstance(res_wrapper, LLMResponse)
    assert res_wrapper.success is True
    assert res_wrapper.token_usage.total_tokens > 0
    assert res_wrapper.prompt_version == "rca-v1"


def test_mock_provider_timeout_exception():
    provider = MockLLMProvider(force_timeout=True)

    with pytest.raises(LLMTimeoutError) as exc_info:
        provider.generate_structured(
            prompt="Test",
            system_prompt="Test",
            response_model=RootCauseAnalysis,
        )

    assert "timed out" in str(exc_info.value)


def test_mock_provider_failure_exception():
    provider = MockLLMProvider(force_failure=True)

    with pytest.raises(LLMProviderError) as exc_info:
        provider.generate_structured(
            prompt="Test",
            system_prompt="Test",
            response_model=RootCauseAnalysis,
        )

    assert "forced failure" in str(exc_info.value)


def test_mock_provider_malformed_schema_exception():
    provider = MockLLMProvider(force_malformed_schema=True)

    with pytest.raises(LLMValidationError) as exc_info:
        provider.generate_structured(
            prompt="Test",
            system_prompt="Test",
            response_model=RootCauseAnalysis,
        )

    assert "Malformed schema" in str(exc_info.value)
