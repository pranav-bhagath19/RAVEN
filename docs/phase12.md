# RAVEN Phase 12 Architecture & Verification
## Adaptive Recovery Intelligence & Offline Policy Optimization

Phase 12 extends RAVEN from static advisory propensity scoring into a deterministic, offline-trained adaptive recovery intelligence system.

---

## 1. Architectural Principles & Data Flow

```
Webhook Ingestion (Deduplicated per tenant_id)
        ↓
State Reconstruction Engine (Tenant-Scoped)
        ↓
RootCauseAnalyst Agent
        ↓
RecoveryPlanner Agent
        ↓
Base Propensity Model (Logistic Regression)
        ↓
Adaptive Recovery Scorer (Combines P(model), global action rates & tenant recovery profiles)
        ↓
Deterministic Integer Expected Value Calculation (paise)
        ↓
Dynamic Policy Engine (Tenant-Active Policy Version & Veto Rules POL_001–POL_007)
        ↓
HMAC-SHA256 Policy Approval Token Issuance
        ↓
Token-Verifying ToolExecutor (Idempotency Store & Circuit Breaker)
        ↓
Verification Agent (T_capture > T_action)
        ↓
DecisionTrace Lineage Snapshot (tenant_id, policy_id, policy_version, policy_hash, intelligence_version)
```

---

## 2. Core Components

1. **`AdaptiveOutcomeDatasetBuilder` (`ml/adaptive/dataset.py`)**: Builds training records from historical recovery outcomes while strictly rejecting post-action leakage fields.
2. **`ActionStatisticsAnalyzer` (`ml/adaptive/action_statistics.py`)**: Computes empirical success rates and confidence intervals per action type using integer minor-unit math ($\mathbb{Z}$).
3. **`TenantIntelligenceManager` (`ml/adaptive/tenant_intelligence.py`)**: Generates tenant-scoped recovery profiles (`tenant_id`) ensuring zero cross-tenant data contamination.
4. **`AdaptiveRecoveryScorer` (`ml/adaptive/scorer.py`)**: Calibrates action probability $P \in [0.0, 1.0]$ using deterministic versioned weights and 4-tier data sufficiency fallback cascades (`ADAPTIVE_ML` $\rightarrow$ `GLOBAL_STATISTICAL_FALLBACK` $\rightarrow$ `PROPENSITY_FALLBACK` $\rightarrow$ `DETERMINISTIC_FALLBACK`).
5. **`CalibrationAnalyzer` (`ml/adaptive/calibration.py`)**: Calculates Brier Score and Expected Calibration Error (ECE).
6. **`DriftDetector` (`ml/adaptive/drift.py`)**: Monitors Population Stability Index (PSI) distribution shift (observational only).
7. **`OfflinePolicyOptimizer` (`ml/optimization/policy_optimizer.py`)**: Dry-run policy simulator calculating hypothetical recovery rates and net EV without production side effects.
8. **`CounterfactualEvaluator` (`ml/optimization/counterfactual.py`)**: Evaluates counterfactual hypotheses labeled clearly as `COUNTERFACTUAL`.
9. **`ModelRegistry` (`ml/models/registry.py`)**: Model lifecycle management (`CANDIDATE`, `CHALLENGER`, `CHAMPION`, `RETIRED`, `REJECTED`) with explicit promotion requirements.
10. **`ChampionChallengerEvaluator` (`ml/evaluation/champion_challenger.py`)**: Compares Champion vs Challenger metrics with canonical SHA-256 report hashing.

---

## 3. Operations Intelligence REST API Endpoints

- `GET /api/v1/operations/intelligence/overview`: Tenant-scoped recovery intelligence analytics.
- `GET /api/v1/operations/intelligence/recovery`: High-level tenant recovery rates.
- `GET /api/v1/operations/intelligence/actions`: Action-level empirical statistics.
- `GET /api/v1/operations/intelligence/tenants/{tenant_id}`: Tenant-scoped recovery profile.
- `GET /api/v1/operations/intelligence/calibration`: Model probability calibration metrics.
- `GET /api/v1/operations/intelligence/drift`: Observational distribution drift report.
- `GET /api/v1/operations/intelligence/models`: List all registered model versions.
- `GET /api/v1/operations/intelligence/models/{model_version}`: Retrieve specific model metadata.
- `GET /api/v1/operations/intelligence/champion-challenger`: Side-by-side Champion vs Challenger evaluation.
- `POST /api/v1/operations/intelligence/policy-optimize`: Dry-run offline policy optimization simulation (Requires `POLICY_WRITE`).

---

## 4. Verification & Interactive Demonstration

```bash
# Run full Pytest suite
python -m pytest tests/ -v

# Run Ruff linter
ruff check domain events simulator policies tools agents ml apps razorpay persistence tests scripts data

# Run MyPy static type checker
mypy domain events simulator policies tools agents ml apps razorpay persistence tests scripts data

# Run 15-Step Interactive Demonstration
python scripts/phase12_demo.py
```
