"""
RAVEN Deterministic Recovery Plan Fallback Module

Provides non-AI deterministic recovery candidate proposals.
Activated when LLM provider fails, times out, or returns invalid schema outputs.
"""

from agents.recovery_planner.models import CandidateActionProposal, RecoveryPlan
from agents.root_cause.models import RootCauseAnalysis
from domain.enums import RecoveryActionType


def evaluate_deterministic_recovery_plan_fallback(
    rca: RootCauseAnalysis,
    payment_id: str,
) -> RecoveryPlan:
    """
    Evaluates candidate recovery proposals deterministically based on root cause analysis.
    """
    root_cause = rca.root_cause.upper()

    if root_cause in ("GATEWAY_TIMED_OUT", "NETWORK_TIMEOUT"):
        proposal = CandidateActionProposal(
            action_type=RecoveryActionType.SMART_RETRY,
            reasoning="Gateway timeout detected. Proposing smart retry with 15-minute exponential backoff.",
            predicted_success_probability=0.85,
            agent_confidence=0.90,
            recommended_delay_seconds=900,
            estimated_cost_minor=0,
            parameters={"delay_seconds": 900},
        )
    elif root_cause in ("INSUFFICIENT_FUNDS", "RECURRING_TOKEN_EXPIRED"):
        proposal = CandidateActionProposal(
            action_type=RecoveryActionType.PAYMENT_LINK_DISPATCH,
            reasoning="Insufficient balance or expired token. Proposing interactive payment link via WhatsApp.",
            predicted_success_probability=0.70,
            agent_confidence=0.85,
            recommended_delay_seconds=0,
            estimated_cost_minor=50,  # 50 paise communication cost
            parameters={"channel": "WHATSAPP"},
        )
    elif root_cause == "AUTHENTICATION_ABANDONED":
        proposal = CandidateActionProposal(
            action_type=RecoveryActionType.FALLBACK_CHANNEL_NOTIFY,
            reasoning="Abandoned checkout authentication. Proposing fallback SMS notification reminder.",
            predicted_success_probability=0.65,
            agent_confidence=0.80,
            recommended_delay_seconds=300,
            estimated_cost_minor=20,  # 20 paise SMS cost
            parameters={"channel": "SMS"},
        )
    else:
        proposal = CandidateActionProposal(
            action_type=RecoveryActionType.ESCALATE_TO_HUMAN,
            reasoning=f"Ambiguous state or unclassified root cause '{root_cause}'. Escalating to merchant operations queue.",
            predicted_success_probability=0.50,
            agent_confidence=0.70,
            recommended_delay_seconds=0,
            estimated_cost_minor=0,
            parameters={"reason": f"Fallback escalation for root cause {root_cause}"},
        )

    return RecoveryPlan(
        payment_id=payment_id,
        proposals=[proposal],
        reasoning_mode="DETERMINISTIC_FALLBACK",
    )
