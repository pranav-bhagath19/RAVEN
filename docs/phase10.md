# RAVEN Phase 10 — Machine Learning Propensity Scoring & Adaptive Recovery Optimization

## 1. Executive Summary
Phase 10 introduces a deterministic, reproducible, and advisory Machine Learning (ML) Propensity Scoring layer to RAVEN. The propensity scoring engine predicts action recovery success probabilities $P(\text{success} \mid \text{state}, \text{action}) \in [0.0, 1.0]$ for candidate actions proposed by the `RecoveryPlanner`.

The ML layer is strictly **ADVISORY ONLY**. It has zero side-effect execution authority, zero token minting permission, and zero ability to override `PolicyEngine` vetoes.

---

## 2. Architecture & Pipeline

```
Payment Failure
      │
      ▼
State Reconstruction
      │
      ▼
Root Cause Analyst
      │
      ▼
Candidate Recovery Actions
      │
      ▼
Feature Pipeline V1 (FeatureSchemaV1)
      │
      ▼
Logistic Regression Propensity Model
      │
      ▼
P(success | state, action) ∈ [0.0, 1.0]
      │
      ▼
Deterministic Expected Value Calculator (paise minor units)
      │
      ▼
PolicyEngine Veto Boundary (POL_001 – POL_007)
      │
      ├── BLOCKED / ESCALATED
      └── APPROVED
                │
                ▼
       PolicyApprovalToken (HMAC-SHA256)
                │
                ▼
          ToolExecutor
                │
                ▼
            Verification
```

---

## 3. Key Components

### 3.1 Feature Schema & Leakage Prevention (`ml/features/schema.py`)
- `FeatureSchemaV1`: Explicit numerical features (`amount_minor`, `attempts_count`) and categorical attributes (`currency`, `error_code`, `root_cause`, `action_type`, `merchant_status`, `customer_opt_out`, `is_systemic_downtime`).
- **Leakage Guard**: Explicitly rejects forbidden post-action fields (`is_recovered`, `recovered_amount_minor`, `verification_status`, etc.) to prevent target leakage.

### 3.2 Feature Pipeline (`ml/features/pipeline.py`)
- `FeaturePipelineV1`: Transforms raw inputs into fixed-length 1D/2D float64 numpy feature vectors using deterministic categorical maps.

### 3.3 Dataset Builder (`ml/dataset.py`)
- `MLDatasetBuilder`: Builds training datasets from synthetic scenario streams or operational logs.
- Enforces strict separation of `FEATURES`, `TARGET` (`is_recovered`), `IDENTIFIERS`, and `GROUND_TRUTH`.
- Chronological train/validation/test splitting (60% Train, 20% Val, 20% Test).

### 3.4 Propensity Model (`ml/models/propensity.py`)
- `LogisticRegressionPropensityModel`: Supervised classifier predicting $P(\text{success}) \in [0.0, 1.0]$.
- Enforces strict validation rejecting NaN, Infinity, $<0$, or $>1$.

### 3.5 Artifact Management (`ml/models/artifact.py`)
- `ModelArtifactManager`: Manages model serialization and SHA-256 artifact hashing (`compute_artifact_hash`).
- Detects tampered, corrupted, or incompatible artifacts to trigger deterministic fallback.

### 3.6 RecoveryPlanner & Deterministic EV Boundary (`agents/recovery_planner/`)
- `RecoveryPlanner`: Incorporates ML propensity predictions into candidate action proposals.
- Expected Value calculation remains pure integer minor units:
  $$\text{EV} = \text{round}(P(\text{success}) \times \text{amount\_minor}) - \text{cost\_minor}$$

### 3.7 Deterministic Fallback Resilience
- On any model error, missing artifact, invalid schema, or inference exception, RAVEN automatically sets `reasoning_mode = "DETERMINISTIC_FALLBACK"` and continues safely through the `PolicyEngine`.

---

## 4. Operational API Endpoints
- `GET /api/v1/operations/ml/models` (Requires `OPERATIONS_READ`)
- `GET /api/v1/operations/ml/models/{model_version}` (Requires `OPERATIONS_READ`)
- `GET /api/v1/operations/ml/metrics` (Requires `OPERATIONS_READ`)

---

## 5. Security & Verification
- 15/15 Security boundary tests verified in `tests/phase10/test_ml_security_boundaries.py`.
- 4-Way comparative benchmark suite verified in `tests/phase10/test_ml_benchmark.py`.
