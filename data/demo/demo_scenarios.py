"""
RAVEN Deterministic Demo Dataset Generator

Generates 15 deterministic demonstration scenarios covering all recovery pathways,
policy blocks, human escalations, attack rejections, and verification attributions.
"""

from typing import Any


def get_demo_scenarios() -> list[dict[str, Any]]:
    """Returns catalog of 15 deterministic demo scenario definitions."""
    return [
        {
            "scenario_id": "demo_1_successful_recovery",
            "name": "Scenario 1: Transient Timeout Smart Retry",
            "payment_id": "pay_demo_transient_1",
            "amount_minor": 250000,
            "error_code": "GATEWAY_TIMED_OUT",
            "expected_policy": "APPROVED",
            "expected_action": "SMART_RETRY",
            "expected_attribution": "RAVEN_ATTRIBUTED",
        },
        {
            "scenario_id": "demo_2_captured_payment_blocked",
            "name": "Scenario 2: Captured Payment Terminal Guard (POL_001)",
            "payment_id": "pay_demo_captured_2",
            "amount_minor": 150000,
            "error_code": None,
            "status": "captured",
            "expected_policy": "BLOCKED",
            "expected_rule": "POL_001",
        },
        {
            "scenario_id": "demo_3_ambiguous_payment_escalated",
            "name": "Scenario 3: Ambiguous Payment State Guard (POL_002)",
            "payment_id": "pay_demo_ambiguous_3",
            "amount_minor": 180000,
            "error_code": "PENDING_VERIFICATION",
            "status": "ambiguous",
            "expected_policy": "ESCALATE_TO_HUMAN",
            "expected_rule": "POL_002",
        },
        {
            "scenario_id": "demo_4_high_value_escalated",
            "name": "Scenario 4: High-Value Transaction Boundary (POL_004)",
            "payment_id": "pay_demo_high_value_4",
            "amount_minor": 1500000,  # ₹15,000 > ₹10,000 threshold
            "error_code": "GATEWAY_TIMED_OUT",
            "expected_policy": "ESCALATE_TO_HUMAN",
            "expected_rule": "POL_004",
        },
        {
            "scenario_id": "demo_5_low_confidence_escalated",
            "name": "Scenario 5: Low Confidence Score Guard (POL_005)",
            "payment_id": "pay_demo_low_conf_5",
            "amount_minor": 200000,
            "error_code": "UNKNOWN_DECLINE_CODE",
            "agent_confidence": 0.50,  # 0.50 < 0.75 threshold
            "expected_policy": "ESCALATE_TO_HUMAN",
            "expected_rule": "POL_005",
        },
        {
            "scenario_id": "demo_6_max_attempts_blocked",
            "name": "Scenario 6: Max Attempt Limit Guard (POL_003)",
            "payment_id": "pay_demo_max_attempts_6",
            "amount_minor": 100000,
            "error_code": "GATEWAY_TIMED_OUT",
            "attempts_count": 3,
            "expected_policy": "BLOCKED",
            "expected_rule": "POL_003",
        },
        {
            "scenario_id": "demo_7_customer_opt_out_blocked",
            "name": "Scenario 7: Customer Communication Opt-Out (POL_006)",
            "payment_id": "pay_demo_opt_out_7",
            "amount_minor": 300000,
            "error_code": "INSUFFICIENT_FUNDS",
            "customer_opt_out": True,
            "expected_policy": "BLOCKED",
            "expected_rule": "POL_006",
        },
        {
            "scenario_id": "demo_8_bank_downtime_blocked",
            "name": "Scenario 8: Systemic Bank Downtime Guard (POL_007)",
            "payment_id": "pay_demo_bank_downtime_8",
            "amount_minor": 120000,
            "error_code": "GATEWAY_TIMED_OUT",
            "bank_downtime_rate": 0.55,  # 55% > 40% threshold
            "expected_policy": "BLOCKED",
            "expected_rule": "POL_007",
        },
        {
            "scenario_id": "demo_9_llm_fallback",
            "name": "Scenario 9: LLM Failure Deterministic Fallback",
            "payment_id": "pay_demo_llm_fallback_9",
            "amount_minor": 200000,
            "error_code": "GATEWAY_TIMED_OUT",
            "force_llm_failure": True,
            "expected_mode": "DETERMINISTIC_FALLBACK",
        },
        {
            "scenario_id": "demo_10_forged_token_rejected",
            "name": "Scenario 10: Cryptographic Forged Token Rejection",
            "payment_id": "pay_demo_forged_token_10",
            "amount_minor": 100000,
            "forged_token": True,
            "expected_result": "REJECTED_POLICY_VIOLATION",
        },
        {
            "scenario_id": "demo_11_duplicate_webhook_ignored",
            "name": "Scenario 11: Webhook Deduplication Engine Safeguard",
            "payment_id": "pay_demo_dup_webhook_11",
            "amount_minor": 100000,
            "duplicate_delivery": True,
            "expected_result": "DUPLICATE_ACCEPTED",
        },
        {
            "scenario_id": "demo_12_duplicate_tool_execution_ignored",
            "name": "Scenario 12: Tool Executor Idempotency Replay Safeguard",
            "payment_id": "pay_demo_dup_tool_12",
            "amount_minor": 100000,
            "duplicate_execution": True,
            "expected_result": "CACHED_IDEMPOTENT_REPLAY",
        },
        {
            "scenario_id": "demo_13_organic_recovery_attribution",
            "name": "Scenario 13: Organic Customer Retry Attribution",
            "payment_id": "pay_demo_organic_13",
            "amount_minor": 100000,
            "organic_retry": True,
            "expected_attribution": "ORGANIC_CUSTOMER_RETRY",
        },
        {
            "scenario_id": "demo_14_no_recovery",
            "name": "Scenario 14: Hard Decline No Recovery",
            "payment_id": "pay_demo_no_recovery_14",
            "amount_minor": 100000,
            "error_code": "CARD_STOLEN",
            "expected_policy": "BLOCKED",
            "expected_attribution": "NO_RECOVERY",
        },
        {
            "scenario_id": "demo_15_pre_existing_recovery",
            "name": "Scenario 15: Pre-Existing Captured Payment",
            "payment_id": "pay_demo_pre_existing_15",
            "amount_minor": 100000,
            "status": "captured",
            "expected_attribution": "PRE_EXISTING_RECOVERY",
        },
    ]
