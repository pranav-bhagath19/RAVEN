"""
RAVEN Recovery Planner Agent Module

Proposes candidate recovery interventions based on root cause analysis and context.
Supports ML propensity scoring and Adaptive Recovery Intelligence layers for candidate ranking
while enforcing deterministic Expected Value calculation in integer minor units (paise).
Automatically falls back to deterministic heuristics on failure or invalid output.
"""

from typing import Any
from agents.common.errors import LLMProviderError, LLMTimeoutError, LLMValidationError
from agents.common.prompts import RECOVERY_PLANNER_PROMPT_VERSION, RECOVERY_PLANNER_SYSTEM_PROMPT
from agents.common.provider import BaseLLMProvider
from agents.recovery_planner.expected_value import calculate_expected_value
from agents.recovery_planner.fallback import evaluate_deterministic_recovery_plan_fallback
from agents.recovery_planner.models import CandidateActionProposal, RecoveryPlan
from agents.root_cause.models import RootCauseAnalysis
from domain.entities.customer import Customer
from domain.entities.merchant import Merchant
from domain.entities.payment import Payment
from ml.adaptive.scorer import AdaptiveRecoveryScorer
from ml.features.pipeline import FeaturePipelineV1
from ml.models.propensity import BasePropensityModel


class RecoveryPlanner:
    """
    Recovery Planner Agent generating candidate proposals with deterministic Expected Value ranking.
    Incorporates ML propensity scoring and Adaptive Recovery Intelligence for action probability estimation.
    """

    def __init__(
        self,
        propensity_model: BasePropensityModel | None = None,
        adaptive_scorer: AdaptiveRecoveryScorer | None = None,
    ) -> None:
        self.propensity_model = propensity_model
        self.adaptive_scorer = adaptive_scorer
        self.feature_pipeline = FeaturePipelineV1()

    def plan_recovery(
        self,
        rca: RootCauseAnalysis,
        payment: Payment | None,
        customer: Customer | None = None,
        merchant: Merchant | None = None,
        context: dict[str, Any] | None = None,
        provider: BaseLLMProvider | None = None,
    ) -> tuple[RecoveryPlan, list[dict[str, Any]]]:
        """
        Generates candidate recovery proposals and ranks them deterministically by Expected Value.
        Returns tuple of (RecoveryPlan, list of ExpectedValue dictionary summaries).
        """
        payment_id = payment.id if payment else "pay_unknown"
        amount_minor = payment.amount.amount_minor if (payment and hasattr(payment, "amount") and payment.amount) else 0

        attempts_list = getattr(payment, "attempts", []) if payment else []
        attempts_count = len(attempts_list)
        last_attempt = attempts_list[-1] if attempts_list else None
        error_code = getattr(last_attempt, "error_code", None) or getattr(payment, "error_code", None) or "UNKNOWN"

        currency = payment.currency if (payment and hasattr(payment, "currency")) else "INR"
        merchant_status = merchant.status.value if (merchant and hasattr(merchant.status, "value")) else (merchant.status if merchant else "active")
        customer_opt_out = customer.communication_preferences.opt_out if (customer and hasattr(customer, "communication_preferences")) else False

        reasoning_mode = "DETERMINISTIC_FALLBACK"
        fallback_reason: str | None = None

        if not provider:
            plan = evaluate_deterministic_recovery_plan_fallback(rca, payment_id)
        else:
            prompt_context = {
                "payment_id": payment_id,
                "root_cause": rca.root_cause,
                "recoverability": rca.recoverability,
                "explanation": rca.explanation,
                "amount_minor": amount_minor,
                "customer_opt_out": customer_opt_out,
            }
            prompt = (
                f"Propose candidate recovery actions for the following failure analysis:\n"
                f"{prompt_context}"
            )

            try:
                plan, _ = provider.generate_structured(
                    prompt=prompt,
                    system_prompt=RECOVERY_PLANNER_SYSTEM_PROMPT,
                    response_model=RecoveryPlan,
                    prompt_version=RECOVERY_PLANNER_PROMPT_VERSION,
                )
                reasoning_mode = "LLM"
            except (LLMProviderError, LLMValidationError, LLMTimeoutError, Exception) as exc:
                plan = evaluate_deterministic_recovery_plan_fallback(rca, payment_id)
                fallback_reason = f"LLM provider error: {exc}"

        # ML Propensity & Adaptive Scoring Phase (Advisory Only)
        if self.propensity_model is not None:
            try:
                for proposal in plan.proposals:
                    act_val = proposal.action_type.value if hasattr(proposal.action_type, "value") else str(proposal.action_type)
                    feat_dict = {
                        "amount_minor": amount_minor,
                        "attempts_count": attempts_count,
                        "currency": currency,
                        "error_code": error_code,
                        "root_cause": rca.root_cause,
                        "action_type": act_val,
                        "merchant_status": str(merchant_status),
                        "customer_opt_out": customer_opt_out,
                        "is_systemic_downtime": (rca.root_cause == "SYSTEMIC_BANK_DOWNTIME"),
                    }
                    vec = self.feature_pipeline.transform_single(feat_dict)
                    base_prob = self.propensity_model.predict_probability(vec)

                    if self.adaptive_scorer:
                        score_res = self.adaptive_scorer.score(
                            base_propensity=base_prob,
                            action_type=act_val,
                        )
                        proposal.predicted_success_probability = score_res.adaptive_probability
                        reasoning_mode = score_res.reasoning_mode
                    else:
                        proposal.predicted_success_probability = base_prob
                        reasoning_mode = "ML_PROPENSITY"

            except Exception as exc:
                reasoning_mode = "DETERMINISTIC_FALLBACK"
                fallback_reason = f"ML propensity model inference error: {exc}"

        object.__setattr__(plan, "reasoning_mode", reasoning_mode) if hasattr(plan, "reasoning_mode") else None

        # Deterministic EV Calculation & Ranking
        proposals_with_ev: list[tuple[CandidateActionProposal, dict[str, Any]]] = []

        for proposal in plan.proposals:
            prob = (
                proposal.predicted_success_probability
                if proposal.predicted_success_probability is not None
                else proposal.agent_confidence
            )
            cost_minor = getattr(proposal, "estimated_cost_minor", 0)
            ev_obj = calculate_expected_value(
                probability=prob,
                amount_minor=amount_minor,
                cost_minor=cost_minor,
            )
            ev_summary = {
                "action_type": proposal.action_type,
                "expected_value_minor": ev_obj.expected_value_minor,
                "net_expected_value_minor": ev_obj.expected_value_minor,
                "gross_expected_recovery_minor": ev_obj.expected_recovery_minor,
                "probability": ev_obj.probability,
                "cost_minor": ev_obj.cost_minor,
                "reasoning_mode": reasoning_mode,
                "fallback_reason": fallback_reason,
            }
            proposals_with_ev.append((proposal, ev_summary))

        # Sort descending by Net Expected Value (minor units), breaking ties by agent_confidence
        proposals_with_ev.sort(
            key=lambda item: (item[1]["net_expected_value_minor"], item[0].agent_confidence),
            reverse=True,
        )

        plan.proposals = [item[0] for item in proposals_with_ev]
        ev_summaries = [item[1] for item in proposals_with_ev]

        return plan, ev_summaries
