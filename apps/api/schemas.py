"""
RAVEN API Gateway Schemas

Defines strongly typed Pydantic models for HTTP health and webhook ingestion endpoint responses.
"""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Deterministic health check endpoint response payload."""

    status: str = Field("ok", description="Service health status string")
    service: str = Field("raven", description="Service identifier tag")


class WebhookResponse(BaseModel):
    """Structured response returned upon Razorpay webhook ingestion."""

    status: str = Field("accepted", description="Processing status: accepted or duplicate")
    event_id: str = Field(..., description="Processed event ID")
    event_type: str = Field(..., description="Processed event type")
    payment_id: str = Field(..., description="Associated Payment ID")
    duplicate: bool = Field(False, description="Whether event was identified as a duplicate")
    trace_id: str | None = Field(default=None, description="DecisionTrace correlation ID if processed")


class ErrorResponse(BaseModel):
    """Structured error response returned on processing failure or rejection."""

    status: str = Field("error", description="Status tag")
    error_code: str = Field(..., description="Constrained error code")
    message: str = Field(..., description="Sanitized human-readable explanation")
