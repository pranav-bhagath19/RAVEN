"""
RAVEN Baseline Recovery Strategies

Implements AlwaysRetryStrategy (naive retry baseline) and RuleBasedStrategy (conventional rule-based baseline).
Neither baseline uses LLMs, PolicyEngine approval tokens, or AgentOrchestrator.
"""

import time
from domain.enums import RecoveryActionType
from ml.evaluation.models import EvaluationCase, StrategyDecision
from ml.evaluation.strategies import EvaluationStrategy


class AlwaysRetryStrategy(EvaluationStrategy):
    """
    Baseline #1: Always Retry Strategy.
    Naively retries every failed payment immediately without root cause analysis, policy checks, or delay optimization.
    """

    def __init__(self) -> None:
        self.name = "Always Retry"

    def evaluate(self, case: EvaluationCase) -> StrategyDecision:
        start_time = time.perf_counter()

        # Naively request SMART_RETRY on any failure case
        action_type = RecoveryActionType.SMART_RETRY.value
        cost_minor = 0

        # Evaluate execution outcome against scenario conditions
        # Naive retry succeeds ONLY if case is recoverable AND root cause is transient timeout
        is_transient = case.ground_truth_root_cause in ("GATEWAY_TIMED_OUT", "NETWORK_TIMEOUT")
        exec_success = case.ground_truth_recoverable and is_transient

        # Naive retry falsely claims organic recoveries if it blindly executed
        attributed = exec_success or (case.ground_truth_organic_recovery and is_transient)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return StrategyDecision(
            strategy_name=self.name,
            action_type=action_type,
            action_parameters={"delay_seconds": 0},
            decision="APPROVED",
            predicted_recovery_probability=0.50,
            expected_value_minor=case.amount_minor,
            execution_attempted=True,
            execution_success=exec_success,
            execution_cost_minor=cost_minor,
            recovery_attributed=attributed,
            attribution_type="ALWAYS_RETRY_ATTRIBUTED" if attributed else "NONE",
            latency_ms=elapsed_ms,
            root_cause_prediction=None,  # No root cause analysis performed
            policy_violation=False,
        )


class RuleBasedStrategy(EvaluationStrategy):
    """
    Baseline #2: Rule-Based Recovery Strategy.
    Conventional deterministic rule-based recovery using simple error code mapping.
    Does not use LLMs, AgentOrchestrator, PolicyEngine token generation, or DecisionTrace reasoning.
    """

    def __init__(self) -> None:
        self.name = "Rule-Based"

    def evaluate(self, case: EvaluationCase) -> StrategyDecision:
        start_time = time.perf_counter()

        # Extract error code from last event payload if available
        last_evt = case.events[-1] if case.events else None
        err_code = ""
        if last_evt and last_evt.payload:
            err_code = str(last_evt.payload.get("error_code") or "").upper()

        action_type = "NONE"
        cost_minor = 0
        predicted_cause = None

        if "TIMED_OUT" in err_code or "TIMEOUT" in err_code:
            action_type = RecoveryActionType.SMART_RETRY.value
            cost_minor = 0
            predicted_cause = "GATEWAY_TIMED_OUT"
        elif "INSUFFICIENT" in err_code or "TOKEN_EXPIRED" in err_code:
            action_type = RecoveryActionType.PAYMENT_LINK_DISPATCH.value
            cost_minor = 50
            predicted_cause = "INSUFFICIENT_FUNDS"
        elif "ABANDONED" in err_code:
            action_type = RecoveryActionType.FALLBACK_CHANNEL_NOTIFY.value
            cost_minor = 20
            predicted_cause = "AUTHENTICATION_ABANDONED"
        else:
            action_type = "NONE"
            predicted_cause = "UNKNOWN"

        exec_attempted = action_type != "NONE"
        # Rule-based succeeds if selected action matches ground truth optimal action AND case is recoverable
        exec_success = exec_attempted and case.ground_truth_recoverable and (action_type == case.ground_truth_optimal_action)
        attributed = exec_success

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return StrategyDecision(
            strategy_name=self.name,
            action_type=action_type,
            action_parameters={},
            decision="APPROVED" if exec_attempted else "NO_ACTION",
            predicted_recovery_probability=0.70 if exec_attempted else 0.0,
            expected_value_minor=case.amount_minor if exec_attempted else 0,
            execution_attempted=exec_attempted,
            execution_success=exec_success,
            execution_cost_minor=cost_minor if exec_attempted else 0,
            recovery_attributed=attributed,
            attribution_type="RULE_BASED_ATTRIBUTED" if attributed else "NONE",
            latency_ms=elapsed_ms,
            root_cause_prediction=predicted_cause,
            policy_violation=False,
        )
