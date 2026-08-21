"""
RAVEN Bandit Context Builder Module

Constructs deterministic 12-dimensional feature context vectors for Contextual Bandit action selection.
Strictly prevents target leakage by rejecting post-action fields and raising ValueError if detected.
"""

from typing import Any
from pydantic import BaseModel, Field

FORBIDDEN_LEAKAGE_FIELDS: set[str] = {
    "recovered_amount_minor",
    "is_recovered",
    "verification_status",
    "executed_at",
    "tool_result",
    "future_event_id",
    "post_action_status",
    "outcome",
}


class BanditContextVector(BaseModel):
    """Deterministic Bandit Context Vector representation."""

    tenant_id: str = Field(..., description="Authenticated Tenant ID")
    payment_id: str = Field(..., description="Target Payment ID")
    amount_scaled: float = Field(..., ge=0.0, description="Amount in INR scaled by 1,000,000")
    attempts_count: float = Field(..., ge=0.0, description="Previous failure attempts count")
    currency_code_encoded: float = Field(..., description="Encoded currency code (1.0 for INR)")
    error_code_encoded: float = Field(..., description="Encoded failure error code")
    root_cause_encoded: float = Field(..., description="Encoded failure root cause")
    action_type_encoded: float = Field(..., description="Encoded candidate action type")
    merchant_status_encoded: float = Field(..., description="Encoded merchant status")
    customer_opt_out_flag: float = Field(..., description="Customer opt-out flag (0.0 or 1.0)")
    systemic_downtime_flag: float = Field(..., description="Systemic downtime flag (0.0 or 1.0)")
    base_propensity: float = Field(..., ge=0.0, le=1.0, description="Base ML propensity score")
    tenant_action_success_rate: float = Field(..., ge=0.0, le=1.0, description="Tenant empirical action success rate")
    global_action_success_rate: float = Field(..., ge=0.0, le=1.0, description="Global empirical action success rate")
    feature_vector: list[float] = Field(..., description="Ordered 12-dimensional numerical context vector")


class BanditContextBuilder:
    """
    Deterministic pre-action feature builder for Contextual Bandit scoring.
    """

    ERROR_CODE_MAP: dict[str, float] = {
        "UNKNOWN": 0.0,
        "TIMEOUT": 1.0,
        "GATEWAY_ERROR": 2.0,
        "INSUFFICIENT_FUNDS": 3.0,
        "AUTHENTICATION_FAILED": 4.0,
        "BAD_REQUEST": 5.0,
    }

    ROOT_CAUSE_MAP: dict[str, float] = {
        "UNKNOWN": 0.0,
        "TRANSIENT_NETWORK_TIMEOUT": 1.0,
        "SOFT_DECLINE_RETRYABLE": 2.0,
        "SYSTEMIC_BANK_DOWNTIME": 3.0,
        "HARD_DECLINE_NON_RETRYABLE": 4.0,
        "CUSTOMER_OPT_OUT": 5.0,
    }

    ACTION_TYPE_MAP: dict[str, float] = {
        "NO_ACTION": 0.0,
        "SMART_RETRY": 1.0,
        "RETRY_WITH_DELAY": 2.0,
        "RETRY_WITH_ALTERNATIVE_ROUTE": 3.0,
        "PAYMENT_LINK": 4.0,
        "CUSTOMER_NOTIFICATION": 5.0,
        "HUMAN_ESCALATION": 6.0,
    }

    def build_context(
        self,
        raw_record: dict[str, Any],
        base_propensity: float = 0.50,
        tenant_action_rate: float = 0.50,
        global_action_rate: float = 0.50,
    ) -> BanditContextVector:
        """
        Builds a deterministic 12-dimensional context vector from raw record data.
        Raises ValueError if any post-action leakage field is present.
        """
        # Target leakage validation
        detected_leakage = FORBIDDEN_LEAKAGE_FIELDS.intersection(raw_record.keys())
        if detected_leakage:
            raise ValueError(f"Target leakage violation: Post-action fields detected: {sorted(detected_leakage)}")

        tenant_id = str(raw_record.get("tenant_id", "tenant_default"))
        payment_id = str(raw_record.get("payment_id", "pay_unknown"))

        amount_minor = int(raw_record.get("amount_minor", 100000))
        amount_scaled = round(amount_minor / 1000000.0, 4)

        attempts_count = float(raw_record.get("attempts_count", 1))
        currency_code = 1.0 if raw_record.get("currency", "INR") == "INR" else 0.0

        err_str = str(raw_record.get("error_code", "UNKNOWN")).upper()
        error_code_encoded = self.ERROR_CODE_MAP.get(err_str, 0.0)

        rc_str = str(raw_record.get("root_cause", "UNKNOWN")).upper()
        root_cause_encoded = self.ROOT_CAUSE_MAP.get(rc_str, 0.0)

        act_str = str(raw_record.get("action_type", "SMART_RETRY")).upper()
        action_type_encoded = self.ACTION_TYPE_MAP.get(act_str, 1.0)

        merchant_status_encoded = 1.0 if str(raw_record.get("merchant_status", "ACTIVE")).upper() == "ACTIVE" else 0.0
        customer_opt_out_flag = 1.0 if raw_record.get("customer_opt_out_flag", False) else 0.0
        systemic_downtime_flag = 1.0 if raw_record.get("systemic_downtime_flag", False) else 0.0

        p_base = round(max(0.0, min(1.0, float(base_propensity))), 4)
        p_tenant = round(max(0.0, min(1.0, float(tenant_action_rate))), 4)
        p_global = round(max(0.0, min(1.0, float(global_action_rate))), 4)

        vector = [
            amount_scaled,
            attempts_count,
            currency_code,
            error_code_encoded,
            root_cause_encoded,
            action_type_encoded,
            merchant_status_encoded,
            customer_opt_out_flag,
            systemic_downtime_flag,
            p_base,
            p_tenant,
            p_global,
        ]

        return BanditContextVector(
            tenant_id=tenant_id,
            payment_id=payment_id,
            amount_scaled=amount_scaled,
            attempts_count=attempts_count,
            currency_code_encoded=currency_code,
            error_code_encoded=error_code_encoded,
            root_cause_encoded=root_cause_encoded,
            action_type_encoded=action_type_encoded,
            merchant_status_encoded=merchant_status_encoded,
            customer_opt_out_flag=customer_opt_out_flag,
            systemic_downtime_flag=systemic_downtime_flag,
            base_propensity=p_base,
            tenant_action_success_rate=p_tenant,
            global_action_success_rate=p_global,
            feature_vector=vector,
        )
