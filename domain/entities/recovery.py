"""
RAVEN Recovery Domain Entities

Defines RecoveryOpportunity, RecoveryAction, and RecoveryOutcome entities.
Maintains clear separation between Action Representation and Action Execution.
"""

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field
from domain.enums import OpportunityStatus, RecoveryActionType, RecoveryOutcomeStatus
from domain.values.money import Money


class RecoveryOpportunity(BaseModel):
    """
    RecoveryOpportunity entity representing an identified revenue risk case.
    """

    id: str = Field(..., description="Unique Opportunity ID, e.g. opp_01H...")
    merchant_id: str = Field(..., description="Associated Merchant ID")
    payment_id: str = Field(..., description="Associated Payment ID")
    amount_at_risk: Money = Field(..., description="Unrecovered revenue at risk Money object")
    risk_category: str = Field(..., description="Risk taxonomy classification")
    status: OpportunityStatus = Field(OpportunityStatus.OPEN, description="Opportunity status")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp in UTC",
    )


class RecoveryAction(BaseModel):
    """
    RecoveryAction entity representing a candidate or authorized intervention proposal.
    Strictly action representation ONLY—does NOT perform external side-effects directly.
    """

    id: str = Field(..., description="Unique Action ID, e.g. act_01H...")
    opportunity_id: str = Field(..., description="Parent Recovery Opportunity ID")
    action_type: RecoveryActionType = Field(..., description="Intervention strategy category")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Action parameters snapshot")
    expected_recovery_value: Money = Field(..., description="Expected Recovery Value Money object")
    agent_confidence: float = Field(..., ge=0.0, le=1.0, description="Agent confidence score (0.0 to 1.0)")
    policy_decision: str = Field("PENDING", description="Policy engine decision status (APPROVED, BLOCKED, ESCALATED)")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp in UTC",
    )


class RecoveryOutcome(BaseModel):
    """
    RecoveryOutcome entity representing post-intervention verification result.
    """

    id: str = Field(..., description="Unique Outcome ID, e.g. out_01H...")
    opportunity_id: str = Field(..., description="Associated Recovery Opportunity ID")
    action_id: str = Field(..., description="Associated Recovery Action ID")
    status: RecoveryOutcomeStatus = Field(..., description="Outcome verification status")
    is_recovered: bool = Field(False, description="Whether revenue was genuinely recovered")
    recovered_amount: Money = Field(..., description="Amount of revenue recovered Money object")
    verification_method: str = Field("GATEWAY_RECONCILIATION", description="Verification method tag")
    verified_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Verification timestamp in UTC",
    )
