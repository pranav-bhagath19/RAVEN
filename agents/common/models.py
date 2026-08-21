"""
RAVEN Common LLM Request and Response Models
"""

from datetime import datetime, timezone
from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class TokenUsage(BaseModel):
    """Token consumption metadata snapshot."""

    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)


class LLMRequest(BaseModel):
    """Standardized LLM Request wrapper."""

    prompt: str = Field(..., description="User prompt text")
    system_prompt: str = Field(..., description="System instructions")
    prompt_version: str = Field(..., description="Prompt version identifier, e.g. rca-v1")
    model_name: str = Field(default="gpt-4o", description="Target model name")
    provider_name: str = Field(default="mock_provider", description="Target provider name")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Sampling temperature")


class LLMResponse(BaseModel, Generic[T]):
    """Standardized LLM Response wrapper with parsing, latency, and token metrics."""

    parsed_output: T | None = Field(default=None, description="Pydantic parsed response object if successful")
    raw_text: str = Field(default="", description="Raw response text")
    provider_name: str = Field(..., description="Executing provider name")
    model_name: str = Field(..., description="Executing model name")
    prompt_version: str = Field(..., description="Prompt version used")
    latency_ms: float = Field(..., ge=0.0, description="Latency in milliseconds")
    token_usage: TokenUsage = Field(default_factory=lambda: TokenUsage(), description="Token consumption metrics")
    success: bool = Field(..., description="Whether generation and validation succeeded")
    failure_reason: str | None = Field(default=None, description="Explanation if generation/validation failed")
    reasoning_mode: str = Field(default="LLM", description="Reasoning mode: 'LLM' or 'DETERMINISTIC_FALLBACK'")
    executed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response timestamp in UTC",
    )
