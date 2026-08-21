"""
RAVEN Evaluation Strategy Abstractions & Implementations

Defines EvaluationStrategy base class, RavenStrategy, RavenMLPropensityStrategy,
and RavenAdaptiveIntelligenceStrategy.
Ground truth fields are strictly isolated and NEVER exposed to strategy decision logic.
"""

from abc import ABC, abstractmethod
import numpy as np
from agents.common.provider import MockLLMProvider
from agents.orchestrator import AgentOrchestrator
from agents.recovery_planner.planner import RecoveryPlanner
from domain.entities.customer import Customer
from domain.entities.merchant import Merchant
from domain.enums import MerchantStatus
from ml.adaptive.scorer import AdaptiveRecoveryScorer
from ml.dataset import MLDatasetBuilder
from ml.evaluation.models import EvaluationCase, StrategyDecision
from ml.models.propensity import LogisticRegressionPropensityModel
from policies.engine import PolicyEngine
from tools.executor import ToolExecutor


class EvaluationStrategy(ABC):
    """Abstract Base Class for Evaluation Recovery Strategies."""

    name: str

    @abstractmethod
    def evaluate(self, case: EvaluationCase) -> StrategyDecision:
        """Evaluates evaluation case and returns a StrategyDecision."""
        pass


class RavenStrategy(EvaluationStrategy):
    """
    RAVEN Recovery Strategy running complete production pipeline.
    """

    def __init__(self, provider: MockLLMProvider | None = None) -> None:
        self.name = "RAVEN"
        self.policy_engine = PolicyEngine()
        self.tool_executor = ToolExecutor()
        self.orchestrator = AgentOrchestrator(
            policy_engine=self.policy_engine,
            tool_executor=self.tool_executor,
        )
        self.provider = provider or MockLLMProvider()

    def evaluate(self, case: EvaluationCase) -> StrategyDecision:
        merchant = Merchant(
            id="mer_eval",
            name="Eval Merchant",
            currency=case.currency,
            status=MerchantStatus.ACTIVE,
        )
        customer = Customer(
            id="cust_eval",
            merchant_id="mer_eval",
            name="Eval Customer",
            email="eval@example.com",
            phone="+919876543210",
        )

        trace = self.orchestrator.process_payment_failure(
            events=case.events,
            merchant=merchant,
            customer=customer,
            provider=self.provider,
        )

        action_type = "NONE"
        prob = 0.0
        if trace.selected_action:
            act_val = trace.selected_action.get("action_type")
            if act_val:
                action_type = act_val if isinstance(act_val, str) else str(act_val)
            prob = trace.selected_action.get("predicted_success_probability", 0.0) or 0.0

        raw_status = trace.status.value if hasattr(trace.status, "value") else str(trace.status)
        dec_status = "BLOCKED" if raw_status in ("POLICY_BLOCKED", "BLOCKED") else raw_status

        rc_pred = None
        if trace.root_cause_result:
            rc_pred = trace.root_cause_result.get("root_cause")

        return StrategyDecision(
            strategy_name=self.name,
            action_type=action_type,
            action_parameters=trace.selected_action.get("parameters", {}) if trace.selected_action else {},
            decision=dec_status,
            predicted_recovery_probability=float(prob),
            expected_value_minor=trace.value_estimates[0].get("net_expected_value_minor", 0) if trace.value_estimates else 0,
            execution_attempted=raw_status in ("EXECUTED", "VERIFIED"),
            execution_success=raw_status == "VERIFIED",
            execution_cost_minor=0,
            recovery_attributed=raw_status == "VERIFIED",
            attribution_type="RAVEN_ATTRIBUTED" if raw_status == "VERIFIED" else "NONE",
            latency_ms=50.0,
            root_cause_prediction=rc_pred,
            policy_violation=False,
        )


class RavenMLPropensityStrategy(EvaluationStrategy):
    """
    RAVEN ML Strategy incorporating trained Logistic Regression ML Propensity Model.
    """

    def __init__(self, provider: MockLLMProvider | None = None, seed: int = 42) -> None:
        self.name = "RAVEN + ML Propensity"
        self.policy_engine = PolicyEngine()
        self.tool_executor = ToolExecutor()

        builder = MLDatasetBuilder(seed=seed)
        dataset = builder.build_dataset_from_simulator()
        self.model = LogisticRegressionPropensityModel(random_state=seed)
        self.model.fit(np.array(dataset.train_split.feature_matrix), np.array(dataset.train_split.target_vector))

        planner = RecoveryPlanner(propensity_model=self.model)
        self.orchestrator = AgentOrchestrator(
            policy_engine=self.policy_engine,
            tool_executor=self.tool_executor,
            recovery_planner=planner,
        )
        self.provider = provider or MockLLMProvider()

    def evaluate(self, case: EvaluationCase) -> StrategyDecision:
        merchant = Merchant(
            id="mer_eval",
            name="Eval Merchant",
            currency=case.currency,
            status=MerchantStatus.ACTIVE,
        )
        customer = Customer(
            id="cust_eval",
            merchant_id="mer_eval",
            name="Eval Customer",
            email="eval@example.com",
            phone="+919876543210",
        )

        trace = self.orchestrator.process_payment_failure(
            events=case.events,
            merchant=merchant,
            customer=customer,
            provider=self.provider,
        )

        action_type = "NONE"
        prob = 0.0
        if trace.selected_action:
            act_val = trace.selected_action.get("action_type")
            if act_val:
                action_type = act_val if isinstance(act_val, str) else str(act_val)
            prob = trace.selected_action.get("predicted_success_probability", 0.0) or 0.0

        raw_status = trace.status.value if hasattr(trace.status, "value") else str(trace.status)
        dec_status = "BLOCKED" if raw_status in ("POLICY_BLOCKED", "BLOCKED") else raw_status

        rc_pred = None
        if trace.root_cause_result:
            rc_pred = trace.root_cause_result.get("root_cause")

        return StrategyDecision(
            strategy_name=self.name,
            action_type=action_type,
            action_parameters=trace.selected_action.get("parameters", {}) if trace.selected_action else {},
            decision=dec_status,
            predicted_recovery_probability=float(prob),
            expected_value_minor=trace.value_estimates[0].get("net_expected_value_minor", 0) if trace.value_estimates else 0,
            execution_attempted=raw_status in ("EXECUTED", "VERIFIED"),
            execution_success=raw_status == "VERIFIED",
            execution_cost_minor=0,
            recovery_attributed=raw_status == "VERIFIED",
            attribution_type="RAVEN_ATTRIBUTED" if raw_status == "VERIFIED" else "NONE",
            latency_ms=50.0,
            root_cause_prediction=rc_pred,
            policy_violation=False,
        )


class RavenAdaptiveIntelligenceStrategy(EvaluationStrategy):
    """
    RAVEN Phase 12 Strategy incorporating Adaptive Recovery Intelligence layer.
    """

    def __init__(self, provider: MockLLMProvider | None = None, seed: int = 42) -> None:
        self.name = "RAVEN + Adaptive Intelligence"
        self.policy_engine = PolicyEngine()
        self.tool_executor = ToolExecutor()

        builder = MLDatasetBuilder(seed=seed)
        dataset = builder.build_dataset_from_simulator()
        self.model = LogisticRegressionPropensityModel(random_state=seed)
        self.model.fit(np.array(dataset.train_split.feature_matrix), np.array(dataset.train_split.target_vector))

        self.adaptive_scorer = AdaptiveRecoveryScorer()
        planner = RecoveryPlanner(propensity_model=self.model, adaptive_scorer=self.adaptive_scorer)
        self.orchestrator = AgentOrchestrator(
            policy_engine=self.policy_engine,
            tool_executor=self.tool_executor,
            recovery_planner=planner,
        )
        self.provider = provider or MockLLMProvider()

    def evaluate(self, case: EvaluationCase) -> StrategyDecision:
        merchant = Merchant(
            id="mer_eval",
            name="Eval Merchant",
            currency=case.currency,
            status=MerchantStatus.ACTIVE,
        )
        customer = Customer(
            id="cust_eval",
            merchant_id="mer_eval",
            name="Eval Customer",
            email="eval@example.com",
            phone="+919876543210",
        )

        trace = self.orchestrator.process_payment_failure(
            events=case.events,
            merchant=merchant,
            customer=customer,
            provider=self.provider,
        )

        action_type = "NONE"
        prob = 0.0
        if trace.selected_action:
            act_val = trace.selected_action.get("action_type")
            if act_val:
                action_type = act_val if isinstance(act_val, str) else str(act_val)
            prob = trace.selected_action.get("predicted_success_probability", 0.0) or 0.0

        raw_status = trace.status.value if hasattr(trace.status, "value") else str(trace.status)
        dec_status = "BLOCKED" if raw_status in ("POLICY_BLOCKED", "BLOCKED") else raw_status

        rc_pred = None
        if trace.root_cause_result:
            rc_pred = trace.root_cause_result.get("root_cause")

        return StrategyDecision(
            strategy_name=self.name,
            action_type=action_type,
            action_parameters=trace.selected_action.get("parameters", {}) if trace.selected_action else {},
            decision=dec_status,
            predicted_recovery_probability=float(prob),
            expected_value_minor=trace.value_estimates[0].get("net_expected_value_minor", 0) if trace.value_estimates else 0,
            execution_attempted=raw_status in ("EXECUTED", "VERIFIED"),
            execution_success=raw_status == "VERIFIED",
            execution_cost_minor=0,
            recovery_attributed=raw_status == "VERIFIED",
            attribution_type="RAVEN_ATTRIBUTED" if raw_status == "VERIFIED" else "NONE",
            latency_ms=50.0,
            root_cause_prediction=rc_pred,
            policy_violation=False,
        )
