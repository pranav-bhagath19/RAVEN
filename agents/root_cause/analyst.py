"""
RAVEN Root Cause Analyst Agent Module

Invokes LLM provider with sanitized transaction context to analyze payment failures.
Enforces Pydantic validation, structured response parsing, and automatic fallback to deterministic heuristics on failure.
"""

from typing import Any
from agents.common.errors import LLMProviderError, LLMTimeoutError, LLMValidationError
from agents.common.prompts import ROOT_CAUSE_PROMPT_VERSION, ROOT_CAUSE_SYSTEM_PROMPT
from agents.common.provider import BaseLLMProvider
from agents.root_cause.fallback import evaluate_deterministic_root_cause_fallback
from agents.root_cause.models import RootCauseAnalysis
from domain.entities.customer import Customer
from domain.entities.merchant import Merchant
from domain.entities.payment import Payment


class RootCauseAnalyst:
    """
    Root Cause Analyst Agent performing intelligent failure diagnosis with deterministic fallback.
    """

    def analyze(
        self,
        payment: Payment | None,
        attempts: list[Any] | None = None,
        event_timeline: list[dict[str, Any]] | None = None,
        customer: Customer | None = None,
        merchant: Merchant | None = None,
        bank_downtime_rate: float = 0.0,
        provider: BaseLLMProvider | None = None,
        error_code: str | None = None,
        gateway_message: str | None = None,
    ) -> RootCauseAnalysis:
        """
        Analyzes transaction context to produce a validated RootCauseAnalysis.
        Automatically falls back to deterministic heuristic if provider is None or fails.
        """
        if not provider:
            return evaluate_deterministic_root_cause_fallback(
                payment=payment,
                error_code=error_code,
                gateway_message=gateway_message,
                raw_events=event_timeline,
            )

        # Build sanitized context representation
        sanitized_context = {
            "payment_id": payment.id if payment else "pay_unknown",
            "payment_status": payment.status if payment else "FAILED",
            "amount_minor": payment.amount.amount_minor if payment else 0,
            "currency": payment.amount.currency if payment else "INR",
            "attempts_count": len(attempts) if attempts else 0,
            "error_code": error_code or "UNKNOWN",
            "gateway_message": gateway_message or "No message",
            "bank_downtime_rate": bank_downtime_rate,
            "merchant_id": merchant.id if merchant else "mer_unknown",
            "customer_opt_out": customer.communication_preferences.opt_out if customer else False,
            "event_count": len(event_timeline) if event_timeline else 0,
        }

        prompt = (
            f"Analyze the following payment failure context and identify the primary root cause:\n"
            f"{sanitized_context}"
        )

        try:
            rca_result, _ = provider.generate_structured(
                prompt=prompt,
                system_prompt=ROOT_CAUSE_SYSTEM_PROMPT,
                response_model=RootCauseAnalysis,
                prompt_version=ROOT_CAUSE_PROMPT_VERSION,
            )
            # Ensure reasoning_mode is LLM for successful provider response
            object.__setattr__(rca_result, "reasoning_mode", "LLM") if hasattr(rca_result, "reasoning_mode") else None
            return rca_result

        except (LLMProviderError, LLMValidationError, LLMTimeoutError, Exception):
            # Safe Fallback to deterministic heuristic
            return evaluate_deterministic_root_cause_fallback(
                payment=payment,
                error_code=error_code,
                gateway_message=gateway_message,
                raw_events=event_timeline,
            )
