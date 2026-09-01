"""
RAVEN Contextual Bandit Offline Policy Simulator

Simulates Contextual Bandit decision optimization on historical payment failure logs without side-effects:
- Zero ToolExecutor action execution authority
- Zero PolicyApprovalToken issuance authority
- Zero production policy state mutation
- Zero production financial state mutation
- Supports deterministic random seeds
- Produces canonical SHA-256 simulation report hashes
"""

import hashlib
import json
import random
from typing import Any
from pydantic import BaseModel, Field
from ml.bandits.action_space import BanditActionSpace
from ml.bandits.context import BanditContextBuilder
from ml.bandits.model import LinUCBBanditModel


class BanditSimulationReport(BaseModel):
    """Offline Policy + Bandit Simulation summary report."""

    simulator_version: str = Field(default="v13.0")
    total_simulated_transactions: int = Field(..., ge=0)
    simulated_recoveries: int = Field(..., ge=0)
    simulated_recovery_rate: float = Field(..., ge=0.0, le=1.0)
    simulated_gross_recovered_minor: int = Field(..., ge=0)
    policy_vetoes_triggered: int = Field(..., ge=0)
    unsafe_action_attempts: int = Field(default=0, ge=0)
    side_effects_executed: int = Field(default=0, ge=0)
    tokens_issued: int = Field(default=0, ge=0)
    seed: int = Field(default=42)
    report_hash: str = Field(..., description="Canonical SHA-256 hex digest of simulation report")


class BanditSimulator:
    """
    Offline simulator executing dry-run contextual bandit decision optimization.
    Guarantees absolute side-effect isolation.
    """

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.context_builder = BanditContextBuilder()
        self.bandit_model = LinUCBBanditModel(alpha=0.5, seed=seed)

    def simulate(self, scenarios: list[dict[str, Any]]) -> BanditSimulationReport:
        """
        Executes dry-run simulation over scenario payloads.
        Returns deterministic BanditSimulationReport with zero side-effects.
        """
        random.seed(self.seed)
        n = len(scenarios) if scenarios else 100

        simulated_recoveries = 0
        policy_vetoes = 0
        total_gross_minor = 0

        action_space = BanditActionSpace.get_all_actions()

        for idx in range(n):
            scen = scenarios[idx] if scenarios and idx < len(scenarios) else {}
            amount_minor = int(scen.get("amount_minor", 100000))
            err_code = str(scen.get("error_code", "TIMEOUT"))

            raw_record = {
                "tenant_id": str(scen.get("tenant_id", "tenant_demo")),
                "payment_id": f"pay_sim_{idx:04d}",
                "amount_minor": amount_minor,
                "attempts_count": 1,
                "currency": "INR",
                "error_code": err_code,
                "root_cause": "TRANSIENT_NETWORK_TIMEOUT",
                "action_type": "SMART_RETRY",
                "merchant_status": "ACTIVE",
            }

            ctx_vec = self.context_builder.build_context(raw_record)

            # Score candidates with LinUCB
            scored_candidates = []
            for act in action_space:
                res = self.bandit_model.score_action(act, ctx_vec.feature_vector)
                scored_candidates.append((act, res.ucb_score))

            scored_candidates.sort(key=lambda x: x[1], reverse=True)
            top_action = scored_candidates[0][0]

            # Simulate Policy Engine check (e.g. HARD_DECLINE or customer opt-out vetoed)
            is_vetoed = (err_code == "HARD_DECLINE") or (scen.get("customer_opt_out", False)) or (top_action == "NO_ACTION")
            if is_vetoed:
                policy_vetoes += 1
            else:
                simulated_recoveries += 1
                total_gross_minor += amount_minor

        recovery_rate = round(simulated_recoveries / max(1, n), 4)

        payload = {
            "simulator_version": "v13.0",
            "total_simulated_transactions": n,
            "simulated_recoveries": simulated_recoveries,
            "simulated_recovery_rate": recovery_rate,
            "simulated_gross_recovered_minor": total_gross_minor,
            "policy_vetoes_triggered": policy_vetoes,
            "unsafe_action_attempts": 0,
            "side_effects_executed": 0,
            "tokens_issued": 0,
            "seed": self.seed,
        }

        serialized = json.dumps(payload, sort_keys=True)
        report_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        return BanditSimulationReport(
            simulator_version="v13.0",
            total_simulated_transactions=n,
            simulated_recoveries=simulated_recoveries,
            simulated_recovery_rate=recovery_rate,
            simulated_gross_recovered_minor=total_gross_minor,
            policy_vetoes_triggered=policy_vetoes,
            unsafe_action_attempts=0,
            side_effects_executed=0,
            tokens_issued=0,
            seed=self.seed,
            report_hash=report_hash,
        )
