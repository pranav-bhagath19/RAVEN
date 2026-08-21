"""
RAVEN LLM Observability & Telemetry Module

Append-only, in-memory telemetry log for AI reasoning invocations, latency, token usage,
and reasoning mode metrics. Automatically masks sensitive PII and cryptographic tokens.
"""

from datetime import datetime
import re
import threading
from pydantic import BaseModel, Field
from agents.common.models import TokenUsage


def sanitize_pii(text: str) -> str:
    """
    Sanitizes sensitive PII (email addresses, phone numbers, HMAC keys, tokens) from telemetry logs.
    """
    if not text:
        return text

    # Mask emails: j***@domain.com
    text = re.sub(
        r"\b([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b",
        r"\1***@\2",
        text,
    )
    # Mask Indian/International Phone Numbers: +91*****43210
    text = re.sub(r"\+?\d{1,3}[-.\s]?\d{5}[-.\s]?\d{5}", "+XX-XXXXX-XXXXX", text)
    # Mask Secret keys / tokens
    text = re.sub(r"(secret|token|signature)=['\"][^'\"]+['\"]", r"\1='[MASKED]'", text, flags=re.IGNORECASE)
    return text


class LLMInvocationLogEntry(BaseModel):
    """
    Structured record of an LLM invocation or fallback event.
    """

    trace_id: str = Field(..., description="Associated trace ID")
    decision_id: str | None = Field(default=None, description="Associated decision ID")
    agent_name: str = Field(..., description="Agent name (e.g. RootCauseAnalyst)")
    model: str = Field(..., description="Executing model name")
    provider: str = Field(..., description="Executing provider name")
    prompt_version: str = Field(..., description="Prompt version tag")
    started_at: datetime = Field(..., description="Invocation start timestamp in UTC")
    completed_at: datetime = Field(..., description="Invocation completion timestamp in UTC")
    latency_ms: float = Field(..., ge=0.0, description="Latency in milliseconds")
    success: bool = Field(..., description="Whether invocation succeeded")
    failure_reason: str | None = Field(default=None, description="Sanitized failure reason if unsuccessful")
    reasoning_mode: str = Field(..., description="'LLM' or 'DETERMINISTIC_FALLBACK'")
    token_usage: TokenUsage = Field(default_factory=lambda: TokenUsage(), description="Token consumption metrics")
    input_summary: str = Field(..., description="Sanitized input summary")
    output_summary: str = Field(..., description="Sanitized output summary")


class LLMObservabilityTelemetry:
    """
    Thread-safe, append-only telemetry logger for AI observability.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._logs: list[LLMInvocationLogEntry] = []

    def record_invocation(
        self,
        trace_id: str,
        agent_name: str,
        model: str,
        provider: str,
        prompt_version: str,
        started_at: datetime,
        completed_at: datetime,
        latency_ms: float,
        success: bool,
        reasoning_mode: str,
        input_summary: str,
        output_summary: str,
        decision_id: str | None = None,
        failure_reason: str | None = None,
        token_usage: TokenUsage | None = None,
    ) -> LLMInvocationLogEntry:
        """Records sanitized LLM invocation log entry."""
        clean_input = sanitize_pii(input_summary)
        clean_output = sanitize_pii(output_summary)
        clean_failure = sanitize_pii(failure_reason) if failure_reason else None

        entry = LLMInvocationLogEntry(
            trace_id=trace_id,
            decision_id=decision_id,
            agent_name=agent_name,
            model=model,
            provider=provider,
            prompt_version=prompt_version,
            started_at=started_at,
            completed_at=completed_at,
            latency_ms=latency_ms,
            success=success,
            failure_reason=clean_failure,
            reasoning_mode=reasoning_mode,
            token_usage=token_usage or TokenUsage(),
            input_summary=clean_input,
            output_summary=clean_output,
        )

        with self._lock:
            self._logs.append(entry)

        return entry

    def get_logs(self, trace_id: str | None = None) -> list[LLMInvocationLogEntry]:
        """Retrieves invocation log entries filtered by trace_id if provided."""
        with self._lock:
            if trace_id:
                return [entry for entry in self._logs if entry.trace_id == trace_id]
            return list(self._logs)

    def clear(self) -> None:
        """Clears telemetry logs (used in test setup)."""
        with self._lock:
            self._logs.clear()
