"""
RAVEN Deterministic Root Cause Fallback Module

Provides non-AI deterministic heuristics for root cause identification.
Activated when LLM provider fails, times out, or returns invalid schema outputs.
"""

from typing import Any
from agents.root_cause.models import RootCauseAnalysis
from domain.entities.payment import Payment, PaymentStatus


def evaluate_deterministic_root_cause_fallback(
    payment: Payment | None,
    error_code: str | None = None,
    gateway_message: str | None = None,
    raw_events: list[dict[str, Any]] | None = None,
) -> RootCauseAnalysis:
    """
    Evaluates root cause deterministically based on payment status, gateway error codes, and event history.
    """
    payment_id = payment.id if payment else "pay_unknown"
    status = payment.status if payment else PaymentStatus.FAILED
    err = (error_code or "").upper()
    msg = (gateway_message or "").upper()

    evidence_list: list[str] = []
    if raw_events:
        evidence_list = [str(ev.get("event_id")) for ev in raw_events if "event_id" in ev]

    if err == "GATEWAY_TIMED_OUT" or "TIMED OUT" in msg or "TIMEOUT" in msg:
        return RootCauseAnalysis(
            payment_id=payment_id,
            root_cause="GATEWAY_TIMED_OUT",
            explanation="Acquiring bank or gateway timeout occurred during transaction authorization.",
            evidence=evidence_list,
            recoverability="HIGH",
            confidence=0.90,
            contributing_factors=["Network congestion", "Bank gateway latency"],
            recommended_direction="Schedule smart retry with exponential backoff delay.",
            reasoning_mode="DETERMINISTIC_FALLBACK",
        )

    if err in ("BAD_REQUEST_PAYMENT_DECLINED_INSUFFICIENT_FUNDS", "INSUFFICIENT_FUNDS") or "INSUFFICIENT" in msg:
        return RootCauseAnalysis(
            payment_id=payment_id,
            root_cause="INSUFFICIENT_FUNDS",
            explanation="Issuer bank declined payment authorization due to insufficient customer balance.",
            evidence=evidence_list,
            recoverability="MEDIUM",
            confidence=0.85,
            contributing_factors=["Insufficient account balance"],
            recommended_direction="Dispatch interactive payment link or notification to customer.",
            reasoning_mode="DETERMINISTIC_FALLBACK",
        )

    if err == "RECURRING_TOKEN_EXPIRED" or "TOKEN EXPIRED" in msg:
        return RootCauseAnalysis(
            payment_id=payment_id,
            root_cause="RECURRING_TOKEN_EXPIRED",
            explanation="Subscription mandate or recurring payment token has expired.",
            evidence=evidence_list,
            recoverability="MEDIUM",
            confidence=0.95,
            contributing_factors=["Expired card/mandate token"],
            recommended_direction="Dispatch mandate re-authentication payment link.",
            reasoning_mode="DETERMINISTIC_FALLBACK",
        )

    if err == "AUTHENTICATION_ABANDONED" or "ABANDONED" in msg:
        return RootCauseAnalysis(
            payment_id=payment_id,
            root_cause="AUTHENTICATION_ABANDONED",
            explanation="Customer abandoned 3DS authentication flow prior to completion.",
            evidence=evidence_list,
            recoverability="HIGH",
            confidence=0.80,
            contributing_factors=["Customer friction", "Abandoned 3DS challenge"],
            recommended_direction="Dispatch fallback SMS/WhatsApp reminder notification.",
            reasoning_mode="DETERMINISTIC_FALLBACK",
        )

    if status == PaymentStatus.AMBIGUOUS or err == "GATEWAY_STATE_AMBIGUOUS" or "AMBIGUOUS" in msg:
        return RootCauseAnalysis(
            payment_id=payment_id,
            root_cause="GATEWAY_AMBIGUOUS",
            explanation="Gateway authorization state is ambiguous or pending verification.",
            evidence=evidence_list,
            recoverability="LOW",
            confidence=0.70,
            contributing_factors=["Asynchronous webhook delay", "Unconfirmed bank state"],
            recommended_direction="Isolate automated actions and escalate to human operator queue.",
            reasoning_mode="DETERMINISTIC_FALLBACK",
        )

    if err == "ORGANIC_CUSTOMER_RETRY" or "ORGANIC" in msg:
        return RootCauseAnalysis(
            payment_id=payment_id,
            root_cause="ORGANIC_CUSTOMER_RETRY",
            explanation="Customer initiated an organic retry directly on checkout screen.",
            evidence=evidence_list,
            recoverability="NON_RECOVERABLE",
            confidence=0.95,
            contributing_factors=["Customer self-recovery"],
            recommended_direction="No automated recovery action required.",
            reasoning_mode="DETERMINISTIC_FALLBACK",
        )

    # Generic Fallback
    return RootCauseAnalysis(
        payment_id=payment_id,
        root_cause="UNKNOWN_PAYMENT_FAILURE",
        explanation="Unclassified payment failure event requiring investigation.",
        evidence=evidence_list,
        recoverability="MEDIUM",
        confidence=0.50,
        contributing_factors=["Unrecognized error code"],
        recommended_direction="Evaluate candidate recovery actions cautiously.",
        reasoning_mode="DETERMINISTIC_FALLBACK",
    )
