"""
RAVEN Root Cause Analyst Models

Defines RootCauseAnalysis Pydantic model with strict field bounds and recoverability tags.
"""

from typing import Literal
from pydantic import BaseModel, Field, field_validator


class RootCauseAnalysis(BaseModel):
    """
    RootCauseAnalysis output model produced by Root Cause Analyst agent or fallback heuristic.
    """

    payment_id: str = Field(..., description="Target Payment ID")
    root_cause: str = Field(..., description="Identified failure root cause category")
    explanation: str = Field(..., description="Human-readable root cause breakdown")
    evidence: list[str] = Field(default_factory=list, description="IDs/log lines of supporting evidence")
    recoverability: Literal["HIGH", "MEDIUM", "LOW", "NON_RECOVERABLE"] = Field(
        ..., description="Recoverability taxonomy assessment"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0 inclusive")
    contributing_factors: list[str] = Field(default_factory=list, description="Secondary contributing factors")
    recommended_direction: str = Field(..., description="High-level recovery strategy guidance")
    reasoning_mode: Literal["LLM", "DETERMINISTIC_FALLBACK"] = Field(
        "LLM", description="Source of analysis: 'LLM' or 'DETERMINISTIC_FALLBACK'"
    )

    @field_validator("confidence")
    @classmethod
    def validate_confidence_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"Confidence score must be strictly between 0.0 and 1.0, got {v}")
        return v
