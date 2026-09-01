"""
RAVEN Bandit Action Space Module

Defines explicit bounded recovery action identifiers for Contextual Bandit decision optimization.
Strictly prevents open-ended or arbitrary action generation.
"""

from enum import Enum
from pydantic import BaseModel, Field


class BanditActionIdentifier(str, Enum):
    """Bounded set of contextual bandit action identifiers."""

    RETRY_PAYMENT = "RETRY_PAYMENT"
    RETRY_WITH_DELAY = "RETRY_WITH_DELAY"
    RETRY_WITH_ALTERNATIVE_ROUTE = "RETRY_WITH_ALTERNATIVE_ROUTE"
    REQUEST_CUSTOMER_ACTION = "REQUEST_CUSTOMER_ACTION"
    NO_ACTION = "NO_ACTION"


class BanditActionDefinition(BaseModel):
    """Metadata schema for a bandit action."""

    action_id: BanditActionIdentifier = Field(..., description="Stable action identifier")
    description: str = Field(..., description="Action description")
    cost_estimate_minor: int = Field(..., ge=0, description="Estimated execution cost in paise")


class BanditActionSpace:
    """
    Bounded Recovery Action Space Manager.
    Maps RecoveryPlanner RecoveryActionType strings to stable BanditActionIdentifiers.
    """

    DEFAULT_ACTIONS: list[BanditActionDefinition] = [
        BanditActionDefinition(
            action_id=BanditActionIdentifier.RETRY_PAYMENT,
            description="Immediate smart retry over primary gateway",
            cost_estimate_minor=10,
        ),
        BanditActionDefinition(
            action_id=BanditActionIdentifier.RETRY_WITH_DELAY,
            description="Delayed retry after transient network backoff",
            cost_estimate_minor=10,
        ),
        BanditActionDefinition(
            action_id=BanditActionIdentifier.RETRY_WITH_ALTERNATIVE_ROUTE,
            description="Smart retry routed over secondary fallback gateway",
            cost_estimate_minor=25,
        ),
        BanditActionDefinition(
            action_id=BanditActionIdentifier.REQUEST_CUSTOMER_ACTION,
            description="Interactive customer payment link notification",
            cost_estimate_minor=50,
        ),
        BanditActionDefinition(
            action_id=BanditActionIdentifier.NO_ACTION,
            description="Safe no-op action for non-retryable failures",
            cost_estimate_minor=0,
        ),
    ]

    @classmethod
    def get_action_identifiers(cls) -> list[str]:
        """Returns list of stable action identifier string values."""
        return [a.value for a in BanditActionIdentifier]

    @classmethod
    def get_all_actions(cls) -> list[str]:
        """Alias returning list of stable action identifier string values."""
        return cls.get_action_identifiers()

    @classmethod
    def map_recovery_action_to_bandit_action(cls, recovery_action_type: str) -> BanditActionIdentifier:
        """Maps RecoveryActionType string to BanditActionIdentifier."""
        act_upper = str(recovery_action_type).upper()
        if "RETRY" in act_upper:
            if "DELAY" in act_upper:
                return BanditActionIdentifier.RETRY_WITH_DELAY
            if "ROUTE" in act_upper or "ALT" in act_upper:
                return BanditActionIdentifier.RETRY_WITH_ALTERNATIVE_ROUTE
            return BanditActionIdentifier.RETRY_PAYMENT
        if "LINK" in act_upper or "CUSTOMER" in act_upper or "NOTIF" in act_upper:
            return BanditActionIdentifier.REQUEST_CUSTOMER_ACTION
        return BanditActionIdentifier.NO_ACTION
