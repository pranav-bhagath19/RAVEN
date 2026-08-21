"""
RAVEN Secure Tool Executor Module

Enforces cryptographic token verification, context binding checks, idempotency rules,
parameter validation, and simulated tool dispatch.
"""

from datetime import datetime, timezone
from domain.enums import RecoveryActionType
from domain.exceptions import PolicyViolationError
from policies.models import CandidateAction, PolicyDecision
from policies.tokens import DEFAULT_POLICY_SECRET, PolicyApprovalToken, verify_approval_token
from tools.base import BaseTool, ToolResult
from tools.idempotency import IdempotencyStore
from tools.simulated import (
    EscalateToHumanTool,
    FallbackChannelNotifyTool,
    PaymentLinkDispatchTool,
    SmartRetryTool,
)


class ToolExecutor:
    """
    Token-verifying Tool Executor enforcing strict security boundaries.
    """

    def __init__(
        self,
        idempotency_store: IdempotencyStore | None = None,
        secret: str = DEFAULT_POLICY_SECRET,
    ) -> None:
        self.idempotency_store = idempotency_store or IdempotencyStore()
        self.secret = secret
        self.tools: dict[RecoveryActionType, BaseTool] = {
            RecoveryActionType.SMART_RETRY: SmartRetryTool(),
            RecoveryActionType.PAYMENT_LINK_DISPATCH: PaymentLinkDispatchTool(),
            RecoveryActionType.FALLBACK_CHANNEL_NOTIFY: FallbackChannelNotifyTool(),
            RecoveryActionType.ESCALATE_TO_HUMAN: EscalateToHumanTool(),
        }

    def execute_action(
        self,
        action: CandidateAction,
        decision: PolicyDecision,
        approval_token: PolicyApprovalToken | None = None,
        current_time: datetime | None = None,
    ) -> ToolResult:
        """
        Validates approval token, decision bindings, idempotency key, and executes target tool.
        Raises PolicyViolationError if ANY verification check fails.
        """
        # 1. Authorization check
        if decision.decision != "APPROVED":
            raise PolicyViolationError(
                policy_rule_code="EXECUTOR_UNAPPROVED",
                message=f"ToolExecutor rejected execution: PolicyDecision is '{decision.decision}', not APPROVED.",
            )

        token = approval_token or decision.approval_token
        if not token:
            raise PolicyViolationError(
                policy_rule_code="EXECUTOR_MISSING_TOKEN",
                message="ToolExecutor rejected execution: Missing PolicyApprovalToken.",
            )

        # 2. Cryptographic Token Verification
        now = current_time or datetime.now(timezone.utc)
        verify_approval_token(
            token=token,
            expected_payment_id=action.payment_id,
            expected_action_id=action.id,
            expected_action_type=action.action_type,
            expected_idempotency_key=action.idempotency_key,
            current_time=now,
            secret=self.secret,
        )

        # 3. Decision binding check
        if token.decision_id != decision.decision_id:
            raise PolicyViolationError(
                policy_rule_code="TOKEN_DECISION_MISMATCH",
                message=f"Token decision_id '{token.decision_id}' does not match PolicyDecision ID '{decision.decision_id}'.",
            )

        # 4. Idempotency Check
        if self.idempotency_store.is_executed(action.idempotency_key):
            cached_result = self.idempotency_store.get_result(action.idempotency_key)
            return ToolResult(
                tool_name=f"simulated_{str(action.action_type.value if hasattr(action.action_type, 'value') else action.action_type).lower()}",
                action_id=action.id,
                payment_id=action.payment_id,
                status="DUPLICATE",
                payload={
                    "message": f"Idempotency key '{action.idempotency_key}' has already been executed.",
                    "cached_result": cached_result,
                },
            )

        # 5. Resolve Tool
        tool = self.tools.get(action.action_type)
        if not tool:
            raise PolicyViolationError(
                policy_rule_code="UNSUPPORTED_TOOL",
                message=f"No tool registered for action_type '{action.action_type}'.",
            )

        # 6. Validate parameters
        tool.validate_parameters(action.parameters)

        # 7. Execute Tool
        result = tool.execute(
            action_id=action.id,
            payment_id=action.payment_id,
            parameters=action.parameters,
        )

        # 8. Record Idempotency
        self.idempotency_store.record_execution(
            idempotency_key=action.idempotency_key,
            result=result.model_dump(),
        )

        return result
