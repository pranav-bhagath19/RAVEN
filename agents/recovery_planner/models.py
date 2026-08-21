"""
RAVEN Recovery Planner Models

Defines CandidateActionProposal and RecoveryPlan models.
"""

from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator
from domain.enums import RecoveryActionType


class CandidateActionProposal(BaseModel):
    """
    Proposed candidate action from Recovery Planner agent prior to PolicyEngine validation.
    """

    action_type: RecoveryActionType = Field(..., description="Proposed action type enum")
    reasoning: str = Field(..., description="Planner reasoning for proposing action")
    predicted_success_probability: float = Field(
        ..., ge=0.0, le=1.0, description="Predicted success probability between 0.0 and 1.0 inclusive"
    )
    agent_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Agent confidence score between 0.0 and 1.0 inclusive"
    )
    recommended_delay_seconds: int = Field(900, ge=0, description="Recommended delay before execution in seconds")
    estimated_cost_minor: int = Field(0, ge=0, description="Estimated execution cost in integer minor units")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Action parameters dictionary")

    @field_validator("predicted_success_probability", "agent_confidence")
    @classmethod
    def validate_probability_bounds(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"Probability/confidence must be strictly between 0.0 and 1.0 inclusive, got {v}")
        return v


class RecoveryPlan(BaseModel):
    """
    Structured Recovery Plan produced by Recovery Planner agent or fallback.
    """

    payment_id: str = Field(..., description="Target Payment ID")
    proposals: list[CandidateActionProposal] = Field(
        default_factory=list, description="List of proposed candidate actions"
    )
    reasoning_mode: Literal["LLM", "DETERMINISTIC_FALLBACK", "ML_PROPENSITY"] = Field(
        "LLM", description="Source of plan: 'LLM', 'DETERMINISTIC_FALLBACK', or 'ML_PROPENSITY'"
    )
