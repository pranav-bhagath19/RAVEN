"""
RAVEN Policy Approval Token Generator & Verifier

Provides cryptographic HMAC-SHA256 authorization tokens.
Binds decisions, payments, actions, policy versions, and idempotency keys to prevent side-effect bypass.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
from typing import Any
import uuid
from pydantic import BaseModel, Field
from domain.exceptions import PolicyViolationError
from policies.models import POLICY_VERSION

DEFAULT_POLICY_SECRET = "raven_policy_secret_key_v1_production_bound"
DEFAULT_TOKEN_EXPIRY_SECONDS = 300  # 5 minutes


class PolicyApprovalToken(BaseModel):
    """
    Ephemeral cryptographic approval token authorizing side-effect tool execution.
    """

    token_id: str = Field(default_factory=lambda: f"tok_{uuid.uuid4().hex[:12]}", description="Unique Token ID")
    decision_id: str = Field(..., description="Bound Policy Decision ID")
    opportunity_id: str = Field(..., description="Bound Opportunity ID")
    payment_id: str = Field(..., description="Bound Payment ID")
    action_id: str = Field(..., description="Bound Candidate Action ID")
    action_type: str = Field(..., description="Bound Action Type")
    policy_version: str = Field(POLICY_VERSION, description="Bound Policy Version")
    idempotency_key: str = Field(..., description="Bound Idempotency Key")
    issued_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Token issuance timestamp in UTC",
    )
    expires_at: datetime = Field(..., description="Token expiration timestamp in UTC")
    signature: str = Field(..., description="HMAC-SHA256 signature hex digest")

    @staticmethod
    def compute_signature(
        token_id: str,
        decision_id: str,
        opportunity_id: str,
        payment_id: str,
        action_id: str,
        action_type: str,
        policy_version: str,
        idempotency_key: str,
        issued_at: datetime,
        expires_at: datetime,
        secret: str = DEFAULT_POLICY_SECRET,
    ) -> str:
        """
        Computes HMAC-SHA256 signature over token fields string.
        """
        clean_action_type = str(action_type.value if hasattr(action_type, "value") else action_type)
        payload_str = (
            f"{token_id}|{decision_id}|{opportunity_id}|{payment_id}|"
            f"{action_id}|{clean_action_type}|{policy_version}|{idempotency_key}|"
            f"{issued_at.isoformat()}|{expires_at.isoformat()}"
        )
        return hmac.new(
            secret.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()


def generate_approval_token(
    decision_id: str,
    opportunity_id: str,
    payment_id: str,
    action_id: str,
    action_type: Any,
    idempotency_key: str,
    policy_version: str = POLICY_VERSION,
    ttl_seconds: int = DEFAULT_TOKEN_EXPIRY_SECONDS,
    secret: str = DEFAULT_POLICY_SECRET,
    issued_at: datetime | None = None,
) -> PolicyApprovalToken:
    """
    Generates cryptographically signed PolicyApprovalToken.
    """
    token_id = f"tok_{uuid.uuid4().hex[:12]}"
    now = issued_at or datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=ttl_seconds)
    clean_action_type = str(action_type.value if hasattr(action_type, "value") else action_type)

    signature = PolicyApprovalToken.compute_signature(
        token_id=token_id,
        decision_id=decision_id,
        opportunity_id=opportunity_id,
        payment_id=payment_id,
        action_id=action_id,
        action_type=clean_action_type,
        policy_version=policy_version,
        idempotency_key=idempotency_key,
        issued_at=now,
        expires_at=expires_at,
        secret=secret,
    )

    return PolicyApprovalToken(
        token_id=token_id,
        decision_id=decision_id,
        opportunity_id=opportunity_id,
        payment_id=payment_id,
        action_id=action_id,
        action_type=clean_action_type,
        policy_version=policy_version,
        idempotency_key=idempotency_key,
        issued_at=now,
        expires_at=expires_at,
        signature=signature,
    )


def verify_approval_token(
    token: PolicyApprovalToken,
    expected_payment_id: str,
    expected_action_id: str,
    expected_action_type: Any,
    expected_idempotency_key: str,
    current_time: datetime | None = None,
    secret: str = DEFAULT_POLICY_SECRET,
) -> bool:
    """
    Verifies token signature, expiration, and cryptographic bindings.
    Raises PolicyViolationError if invalid or expired.
    """
    if not token or not isinstance(token, PolicyApprovalToken):
        raise PolicyViolationError(
            policy_rule_code="TOKEN_VERIFICATION",
            message="Invalid or missing PolicyApprovalToken instance",
        )

    now = current_time or datetime.now(timezone.utc)
    clean_expected_action_type = str(expected_action_type.value if hasattr(expected_action_type, "value") else expected_action_type)

    # 1. Signature Verification
    expected_sig = PolicyApprovalToken.compute_signature(
        token_id=token.token_id,
        decision_id=token.decision_id,
        opportunity_id=token.opportunity_id,
        payment_id=token.payment_id,
        action_id=token.action_id,
        action_type=token.action_type,
        policy_version=token.policy_version,
        idempotency_key=token.idempotency_key,
        issued_at=token.issued_at,
        expires_at=token.expires_at,
        secret=secret,
    )

    if not hmac.compare_digest(expected_sig, token.signature):
        raise PolicyViolationError(
            policy_rule_code="TOKEN_SIGNATURE",
            message="Token signature verification failed. Token payload has been tampered with or forged.",
        )

    # 2. Expiration Verification
    if now > token.expires_at:
        raise PolicyViolationError(
            policy_rule_code="TOKEN_EXPIRED",
            message=f"PolicyApprovalToken expired at {token.expires_at.isoformat()} (current time: {now.isoformat()}).",
        )

    # 3. Future-issued safeguard
    if token.issued_at > now + timedelta(seconds=60):
        raise PolicyViolationError(
            policy_rule_code="TOKEN_FUTURE_ISSUED",
            message="Token issued_at is in the future. Clock skew or token forgery detected.",
        )

    # 4. Context Binding Checks
    if token.payment_id != expected_payment_id:
        raise PolicyViolationError(
            policy_rule_code="TOKEN_PAYMENT_MISMATCH",
            message=f"Token payment_id '{token.payment_id}' does not match target payment_id '{expected_payment_id}'.",
        )

    if token.action_id != expected_action_id:
        raise PolicyViolationError(
            policy_rule_code="TOKEN_ACTION_MISMATCH",
            message=f"Token action_id '{token.action_id}' does not match target action_id '{expected_action_id}'.",
        )

    if token.action_type != clean_expected_action_type:
        raise PolicyViolationError(
            policy_rule_code="TOKEN_ACTION_TYPE_MISMATCH",
            message=f"Token action_type '{token.action_type}' does not match target action_type '{clean_expected_action_type}'.",
        )

    if token.idempotency_key != expected_idempotency_key:
        raise PolicyViolationError(
            policy_rule_code="TOKEN_IDEMPOTENCY_MISMATCH",
            message=f"Token idempotency_key '{token.idempotency_key}' does not match target idempotency_key '{expected_idempotency_key}'.",
        )

    if token.policy_version != POLICY_VERSION:
        raise PolicyViolationError(
            policy_rule_code="TOKEN_VERSION_MISMATCH",
            message=f"Token policy_version '{token.policy_version}' does not match system policy version '{POLICY_VERSION}'.",
        )

    return True
