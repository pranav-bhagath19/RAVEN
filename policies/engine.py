"""
RAVEN Deterministic Policy Engine

Evaluates CandidateAction models against POL_001 through POL_007.
Holds absolute veto authority and issues cryptographically signed PolicyApprovalToken objects ONLY upon approval.
"""

from datetime import datetime, timezone
import uuid
from policies.models import CandidateAction, POLICY_VERSION, PolicyContext, PolicyDecision, PolicyResult
from policies.rules import ALL_POLICY_RULES
from policies.tokens import DEFAULT_POLICY_SECRET, PolicyApprovalToken, generate_approval_token


class PolicyEngine:
    """
    Deterministic Policy Engine holding absolute veto authority over autonomous actions.
    """

    def __init__(self, secret: str | None = None) -> None:
        self.secret = secret

    def evaluate(
        self,
        action: CandidateAction,
        context: PolicyContext | None = None,
        evaluated_at: datetime | None = None,
    ) -> PolicyDecision:
        """
        Evaluates candidate action against all policy rules deterministically.
        Generates PolicyApprovalToken ONLY when decision is APPROVED.
        """
        ctx = context or PolicyContext()
        now = evaluated_at or datetime.now(timezone.utc)
        decision_id = f"dec_{uuid.uuid4().hex[:12]}"

        evaluations: list[PolicyResult] = []
        blocked_rule: PolicyResult | None = None
        escalated_rule: PolicyResult | None = None

        for rule_fn in ALL_POLICY_RULES:
            result = rule_fn(action, ctx)
            evaluations.append(result)

            if not result.passed:
                if result.decision == "BLOCKED" and not blocked_rule:
                    blocked_rule = result
                elif result.decision == "ESCALATE_TO_HUMAN" and not escalated_rule:
                    escalated_rule = result

        if blocked_rule:
            final_decision = "BLOCKED"
            blocking_policy_id = blocked_rule.policy_id
            reason_summary = f"BLOCKED by {blocked_rule.policy_id}: {blocked_rule.reason}"
            approval_token: PolicyApprovalToken | None = None
        elif escalated_rule:
            final_decision = "ESCALATE_TO_HUMAN"
            blocking_policy_id = escalated_rule.policy_id
            reason_summary = f"ESCALATED to human by {escalated_rule.policy_id}: {escalated_rule.reason}"
            approval_token = None
        else:
            final_decision = "APPROVED"
            blocking_policy_id = None
            reason_summary = "All policy rules evaluated and satisfied."

            # Generate signed PolicyApprovalToken ONLY when APPROVED
            token_secret = self.secret or DEFAULT_POLICY_SECRET
            approval_token = generate_approval_token(
                decision_id=decision_id,
                opportunity_id=action.opportunity_id,
                payment_id=action.payment_id,
                action_id=action.id,
                action_type=action.action_type,
                idempotency_key=action.idempotency_key,
                policy_version=POLICY_VERSION,
                secret=token_secret,
                issued_at=now,
            )

        return PolicyDecision(
            decision_id=decision_id,
            action_id=action.id,
            opportunity_id=action.opportunity_id,
            payment_id=action.payment_id,
            decision=final_decision,
            policy_version=POLICY_VERSION,
            evaluated_at=now,
            policy_evaluations=evaluations,
            blocked_by_policy_id=blocking_policy_id,
            reason=reason_summary,
            approval_token=approval_token,
        )
