"""
RAVEN Policy Rules Definitions (POL_001 through POL_007)

Defines individual deterministic policy rule functions.
"""

from domain.enums import PaymentStatus, RecoveryActionType
from policies.models import CandidateAction, POLICY_VERSION, PolicyContext, PolicyResult


class PolicyMetadata:
    """Policy rule documentation metadata."""

    def __init__(self, policy_id: str, name: str, description: str, decision_type: str) -> None:
        self.policy_id = policy_id
        self.name = name
        self.description = description
        self.decision_type = decision_type


def get_registered_policies() -> dict[str, PolicyMetadata]:
    """Returns dictionary of registered PolicyEngine rules metadata."""
    return {
        "POL_001": PolicyMetadata("POL_001", "Terminal Captured Payment Guard", "Blocks recovery actions if payment is CAPTURED or REFUNDED.", "BLOCKED"),
        "POL_002": PolicyMetadata("POL_002", "Ambiguous State Isolation Guard", "Isolates automated actions and escalates to human if state is AMBIGUOUS.", "ESCALATE_TO_HUMAN"),
        "POL_003": PolicyMetadata("POL_003", "Max Recovery Attempt Limit", "Blocks retries when recovery attempt count reaches limit.", "BLOCKED"),
        "POL_004": PolicyMetadata("POL_004", "High-Value Transaction Boundary", "Escalates to human operator if transaction value exceeds high-value threshold.", "ESCALATE_TO_HUMAN"),
        "POL_005": PolicyMetadata("POL_005", "Agent Confidence Threshold Guard", "Escalates to human if agent confidence score is below threshold.", "ESCALATE_TO_HUMAN"),
        "POL_006": PolicyMetadata("POL_006", "Customer Opt-Out & Communication Limit", "Blocks external messaging if customer opted out or exceeded daily limit.", "BLOCKED"),
        "POL_007": PolicyMetadata("POL_007", "Systemic Bank Downtime Guard", "Pauses automated retries during bank outages (>40% failure rate).", "BLOCKED"),
    }


def eval_pol_001_captured_payment_guard(action: CandidateAction, ctx: PolicyContext) -> PolicyResult:
    """
    POL_001: If payment is CAPTURED or REFUNDED, block all recovery actions.
    """
    if ctx.payment and ctx.payment.status in (PaymentStatus.CAPTURED, PaymentStatus.REFUNDED):
        return PolicyResult(
            policy_id="POL_001",
            policy_version=POLICY_VERSION,
            passed=False,
            decision="BLOCKED",
            reason=f"Payment {ctx.payment.id} is in terminal '{ctx.payment.status}' state. All recovery actions blocked.",
        )
    return PolicyResult(
        policy_id="POL_001",
        policy_version=POLICY_VERSION,
        passed=True,
        decision="APPROVED",
        reason="Payment is not in terminal captured/refunded state.",
    )


def eval_pol_002_ambiguous_state_isolation(action: CandidateAction, ctx: PolicyContext) -> PolicyResult:
    """
    POL_002: If payment status is AMBIGUOUS or PENDING, isolate automated actions and escalate to human.
    """
    if ctx.payment and ctx.payment.status in (PaymentStatus.AMBIGUOUS, PaymentStatus.CREATED):
        if action.action_type in (RecoveryActionType.SMART_RETRY, RecoveryActionType.PAYMENT_LINK_DISPATCH, RecoveryActionType.FALLBACK_CHANNEL_NOTIFY):
            return PolicyResult(
                policy_id="POL_002",
                policy_version=POLICY_VERSION,
                passed=False,
                decision="ESCALATE_TO_HUMAN",
                reason=f"Payment {ctx.payment.id} status is '{ctx.payment.status}'. Automated side-effects prohibited until state verification completes.",
            )
    return PolicyResult(
        policy_id="POL_002",
        policy_version=POLICY_VERSION,
        passed=True,
        decision="APPROVED",
        reason="Payment status is confirmed non-ambiguous.",
    )


def eval_pol_003_max_recovery_attempt_cap(action: CandidateAction, ctx: PolicyContext) -> PolicyResult:
    """
    POL_003: If recovery attempts count >= max_recovery_attempts (default 3), block further retries.
    """
    if ctx.attempts_count >= ctx.max_recovery_attempts:
        return PolicyResult(
            policy_id="POL_003",
            policy_version=POLICY_VERSION,
            passed=False,
            decision="BLOCKED",
            reason=f"Recovery attempts count ({ctx.attempts_count}) reached maximum limit ({ctx.max_recovery_attempts}).",
        )
    return PolicyResult(
        policy_id="POL_003",
        policy_version=POLICY_VERSION,
        passed=True,
        decision="APPROVED",
        reason=f"Attempts count ({ctx.attempts_count}) is within limit ({ctx.max_recovery_attempts}).",
    )


def eval_pol_004_high_value_boundary(action: CandidateAction, ctx: PolicyContext) -> PolicyResult:
    """
    POL_004: If transaction amount > high_value_threshold (default ₹10,000), escalate to human.
    """
    amount_minor = ctx.payment.amount.amount_minor if ctx.payment else action.expected_recovery_value.amount_minor
    if amount_minor > ctx.high_value_threshold_minor:
        return PolicyResult(
            policy_id="POL_004",
            policy_version=POLICY_VERSION,
            passed=False,
            decision="ESCALATE_TO_HUMAN",
            reason=f"Transaction amount ({amount_minor} minor units) exceeds high-value threshold ({ctx.high_value_threshold_minor}). Escalating to human operator.",
        )
    return PolicyResult(
        policy_id="POL_004",
        policy_version=POLICY_VERSION,
        passed=True,
        decision="APPROVED",
        reason=f"Transaction amount ({amount_minor} minor units) is within autonomous limit ({ctx.high_value_threshold_minor}).",
    )


def eval_pol_005_low_confidence_threshold(action: CandidateAction, ctx: PolicyContext) -> PolicyResult:
    """
    POL_005: If agent confidence < min_confidence_threshold (default 0.75), escalate to human.
    """
    if action.agent_confidence < ctx.min_confidence_threshold:
        return PolicyResult(
            policy_id="POL_005",
            policy_version=POLICY_VERSION,
            passed=False,
            decision="ESCALATE_TO_HUMAN",
            reason=f"Agent confidence score ({action.agent_confidence:.2f}) is below minimum threshold ({ctx.min_confidence_threshold:.2f}).",
        )
    return PolicyResult(
        policy_id="POL_005",
        policy_version=POLICY_VERSION,
        passed=True,
        decision="APPROVED",
        reason=f"Agent confidence score ({action.agent_confidence:.2f}) satisfies threshold ({ctx.min_confidence_threshold:.2f}).",
    )


def eval_pol_006_customer_opt_out(action: CandidateAction, ctx: PolicyContext) -> PolicyResult:
    """
    POL_006: If customer opted out or daily message cap reached, block external communication actions.
    """
    if action.action_type in (RecoveryActionType.PAYMENT_LINK_DISPATCH, RecoveryActionType.FALLBACK_CHANNEL_NOTIFY):
        if ctx.customer:
            prefs = ctx.customer.communication_preferences
            if prefs.opt_out:
                return PolicyResult(
                    policy_id="POL_006",
                    policy_version=POLICY_VERSION,
                    passed=False,
                    decision="BLOCKED",
                    reason=f"Customer {ctx.customer.id} has opted out of recovery communications.",
                )
            if ctx.daily_messages_sent >= prefs.daily_message_limit:
                return PolicyResult(
                    policy_id="POL_006",
                    policy_version=POLICY_VERSION,
                    passed=False,
                    decision="BLOCKED",
                    reason=f"Daily communication limit ({prefs.daily_message_limit}) reached for customer {ctx.customer.id}.",
                )
    return PolicyResult(
        policy_id="POL_006",
        policy_version=POLICY_VERSION,
        passed=True,
        decision="APPROVED",
        reason="Customer communication consent and limits satisfied.",
    )


def eval_pol_007_systemic_bank_downtime(action: CandidateAction, ctx: PolicyContext) -> PolicyResult:
    """
    POL_007: If bank downtime rate >= 40%, pause automated retries.
    """
    if action.action_type == RecoveryActionType.SMART_RETRY and ctx.bank_downtime_rate >= 0.40:
        return PolicyResult(
            policy_id="POL_007",
            policy_version=POLICY_VERSION,
            passed=False,
            decision="BLOCKED",
            reason=f"Systemic bank downtime error rate ({ctx.bank_downtime_rate * 100:.1f}%) exceeds 40% threshold. Automated retry paused.",
        )
    return PolicyResult(
        policy_id="POL_007",
        policy_version=POLICY_VERSION,
        passed=True,
        decision="APPROVED",
        reason="Bank downtime rate is below systemic threshold.",
    )


ALL_POLICY_RULES = [
    eval_pol_001_captured_payment_guard,
    eval_pol_002_ambiguous_state_isolation,
    eval_pol_003_max_recovery_attempt_cap,
    eval_pol_004_high_value_boundary,
    eval_pol_005_low_confidence_threshold,
    eval_pol_006_customer_opt_out,
    eval_pol_007_systemic_bank_downtime,
]
