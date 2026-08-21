"""
RAVEN LLM Provider Boundary Module

Defines BaseLLMProvider abstraction and MockLLMProvider implementation for offline testing.
Supports structured response validation, latency measurement, token usage tracking, and failure handling.
"""

from abc import ABC, abstractmethod
import time
from typing import Any, Callable, TypeVar
from pydantic import BaseModel, ValidationError
from agents.common.errors import LLMProviderError, LLMTimeoutError, LLMValidationError
from agents.common.models import LLMResponse, TokenUsage

T = TypeVar("T", bound=BaseModel)


class BaseLLMProvider(ABC):
    """Abstract Base Class for LLM Provider adapters."""

    def __init__(self, provider_name: str, default_model: str = "gpt-4o") -> None:
        self.provider_name = provider_name
        self.default_model = default_model

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        system_prompt: str,
        response_model: type[T],
        prompt_version: str = "v1",
        model_name: str | None = None,
        temperature: float = 0.0,
        timeout_seconds: float = 10.0,
    ) -> tuple[T, LLMResponse[T]]:
        """Generates structured response validated against Pydantic model."""
        pass


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic Mock LLM Provider for offline test suite execution and fallback validation.
    Does not make external network or API calls.
    """

    def __init__(
        self,
        provider_name: str = "mock_provider",
        default_model: str = "mock-gpt-4o",
        mock_response_generator: Callable[[str, type[Any]], Any] | None = None,
        force_timeout: bool = False,
        force_failure: bool = False,
        force_malformed_schema: bool = False,
    ) -> None:
        super().__init__(provider_name=provider_name, default_model=default_model)
        self.mock_response_generator = mock_response_generator
        self.force_timeout = force_timeout
        self.force_failure = force_failure
        self.force_malformed_schema = force_malformed_schema

    def generate_structured(
        self,
        prompt: str,
        system_prompt: str,
        response_model: type[T],
        prompt_version: str = "v1",
        model_name: str | None = None,
        temperature: float = 0.0,
        timeout_seconds: float = 10.0,
    ) -> tuple[T, LLMResponse[T]]:
        target_model = model_name or self.default_model

        if self.force_timeout:
            raise LLMTimeoutError(self.provider_name, timeout_seconds)

        if self.force_failure:
            raise LLMProviderError(self.provider_name, "Mock provider forced failure")

        if self.force_malformed_schema:
            raise LLMValidationError(target_model, "Malformed schema output")

        # Custom mock generator or automatic mock object creation
        start_time = time.perf_counter()
        try:
            if self.mock_response_generator:
                mock_data = self.mock_response_generator(prompt, response_model)
                if isinstance(mock_data, response_model):
                    parsed_instance = mock_data
                elif isinstance(mock_data, dict):
                    parsed_instance = response_model.model_validate(mock_data)
                else:
                    raise LLMValidationError(target_model, f"Mock generator returned invalid type {type(mock_data).__name__}")
            else:
                raise LLMProviderError(self.provider_name, "No mock response generator configured for mock provider call")

            elapsed = (time.perf_counter() - start_time) * 1000.0
            resp_ok: LLMResponse[T] = LLMResponse(
                parsed_output=parsed_instance,
                raw_text=parsed_instance.model_dump_json(),
                provider_name=self.provider_name,
                model_name=target_model,
                prompt_version=prompt_version,
                latency_ms=elapsed,
                token_usage=TokenUsage(prompt_tokens=120, completion_tokens=45, total_tokens=165),
                success=True,
                failure_reason=None,
            )
            return parsed_instance, resp_ok

        except ValidationError as e:
            raise LLMValidationError(target_model, f"Pydantic validation error: {str(e)}") from e
