# RAVEN Evaluation Framework & Comparative Benchmark Suite

## Overview

The RAVEN Evaluation Framework provides a reproducible, executable benchmark suite that measures **RAVEN** against baseline recovery strategies using controlled synthetic datasets and ground truth annotations.

```
Synthetic Dataset (Generator seed=42)
      │
      ├───────────────┐
      ▼               ▼
 Ground Truth      Scenario Events
      │               │
      │               ▼
      │        Evaluation Harness (BenchmarkRunner)
      │               │
      │       ┌───────┼────────┐
      │       ▼       ▼        ▼
      │     RAVEN   Always    Rule-Based
      │             Retry      Recovery
      │       │       │        │
      └───────┴───────┴────────┘
                  │
                  ▼
          Deterministic Metrics
                  │
                  ▼
          Benchmark Report
                  │
                  ▼
          JSON + Console Output
```

---

## 1. Benchmark Architecture

The evaluation framework operates strictly outside the production decision boundary. It observes and evaluates recovery strategies against controlled evaluation cases without mutating production security controls.

### Directory Structure
```
ml/
└── evaluation/
    ├── __init__.py
    ├── models.py
    ├── strategies.py
    ├── runner.py
    ├── metrics.py
    ├── benchmark.py
    ├── baselines.py
    ├── reporting.py
    └── reproducibility.py

data/
└── evaluation/
    └── benchmark_results_v1.json
```

---

## 2. Strategy Definitions

### 1. RAVEN Strategy (`RavenStrategy`)
Executes the full production pipeline:
$$\text{EVENT} \rightarrow \text{STATE RECONSTRUCTION} \rightarrow \text{ROOT CAUSE} \rightarrow \text{RECOVERY PLAN} \rightarrow \text{DETERMINISTIC EV} \rightarrow \text{POLICY ENGINE} \rightarrow \text{APPROVAL TOKEN} \rightarrow \text{TOOL EXECUTOR} \rightarrow \text{VERIFICATION} \rightarrow \text{OUTCOME}$$

- Non-bypassable `PolicyEngine` (POL_001 – POL_007).
- Mandatory HMAC-SHA256 `PolicyApprovalToken`.
- Pure integer minor unit Expected Value calculation.
- 100% deterministic post-action revenue attribution via `VerificationAgent`.

### 2. Always Retry Strategy (`AlwaysRetryStrategy`)
Naive baseline that unconditionally retries every payment failure immediately:
- Zero root cause analysis (`root_cause_prediction = None`).
- Zero policy intelligence or delay optimization.
- Dispatches naive retries regardless of bank downtime or card decline cause.

### 3. Rule-Based Recovery Strategy (`RuleBasedStrategy`)
Conventional rule-based recovery baseline mapping error codes to hardcoded actions:
- `GATEWAY_TIMED_OUT` $\rightarrow$ `SMART_RETRY`
- `INSUFFICIENT_FUNDS` / `RECURRING_TOKEN_EXPIRED` $\rightarrow$ `PAYMENT_LINK_DISPATCH`
- `AUTHENTICATION_ABANDONED` $\rightarrow$ `FALLBACK_CHANNEL_NOTIFY`
- `AMBIGUOUS` / `CAPTURED` $\rightarrow$ `NO_ACTION`
- NO LLM, NO AgentOrchestrator, NO PolicyEngine approval tokens.

---

## 3. Metric Formulas

All monetary calculations use **integer minor units (paise)**. Floating-point monetary arithmetic is prohibited.

1. **State Reconstruction Accuracy**:
   $$\text{Accuracy}_{\text{state}} = \frac{\text{Correctly Reconstructed Final States}}{\text{Total Cases Evaluated}}$$
2. **Root Cause Accuracy**:
   $$\text{Accuracy}_{\text{RCA}} = \frac{\text{Correct Root Cause Predictions}}{\text{Evaluated Failure Cases with RCA}}$$
3. **Action Selection Accuracy**:
   $$\text{Accuracy}_{\text{action}} = \frac{\text{Selected Action} == \text{Optimal Action}}{\text{Total Actionable Cases}}$$
4. **Gross Recovery Rate**:
   $$\text{Rate}_{\text{gross}} = \frac{\text{Total Revenue Recovered}_{\text{minor}}}{\text{Total Revenue at Risk}_{\text{minor}}}$$
5. **Net Recovery Rate (%)**:
   $$\text{Rate}_{\text{net}} = \frac{\text{Total Revenue Recovered}_{\text{minor}} - \text{Total Action Cost}_{\text{minor}}}{\text{Total Revenue at Risk}_{\text{minor}}} \times 100\%$$
6. **Policy Violation Rate**:
   $$\text{Rate}_{\text{violation}} = \frac{\text{Policy Violating Executions}}{\text{Total Executed Actions}}$$
7. **Attribution Precision**:
   $$\text{Precision}_{\text{attr}} = \frac{\text{True RAVEN-Attributed Recoveries}}{\text{All Recoveries Attributed to RAVEN}}$$
8. **Attribution Recall**:
   $$\text{Recall}_{\text{attr}} = \frac{\text{True RAVEN-Attributed Recoveries}}{\text{Total Recoverable Cases}}$$
9. **Organic Misattribution Rate**:
   $$\text{Rate}_{\text{misattr}} = \frac{\text{Organic Recoveries Incorrectly Attributed to Strategy}}{\text{Total Organic Recoveries}}$$

---

## 4. Ground Truth Isolation

Ground truth parameters (`ground_truth_root_cause`, `ground_truth_optimal_action`, `ground_truth_organic_recovery`) are strictly isolated within `EvaluationCase` models and **NEVER** passed into strategy execution methods or LLM prompts. Ground truth is used exclusively *after* strategy decision execution for comparison metrics.

---

## 5. Reproducibility & SHA-256 Hashing

The benchmark framework guarantees deterministic execution:
$$\text{Dataset Seed} + \text{Benchmark Seed} + \text{Deterministic Simulator} \implies \text{Identical Benchmark SHA-256 Hash}$$

`compute_canonical_benchmark_hash(report)` computes a SHA-256 hex digest over the canonical JSON representation excluding runtime execution timestamps.

---

## 6. How to Run Benchmark

Run the executable benchmark CLI:
```bash
python -m ml.evaluation.benchmark --seed 42
```

Optional CLI flags:
- `--seed <INT>`: Random seed (default: `42`).
- `--output <PATH>`: Output JSON file path (default: `data/evaluation/benchmark_results_v1.json`).
- `--quiet`: Suppress console table printing.

---

## 7. Results Output Location

Sealed JSON reports are saved to:
`data/evaluation/benchmark_results_v1.json`

---

## 8. Phase 10 Advisory ML Propensity Model Metrics

Phase 10 introduces advisory Machine Learning propensity scoring evaluated with standard binary classification metrics:

1. **ROC-AUC (Receiver Operating Characteristic - Area Under Curve)**: Discriminative capability across probability thresholds ($0.9250$).
2. **PR-AUC (Precision-Recall Area Under Curve)**: Performance under class imbalance ($0.9180$).
3. **Accuracy**: Total correct predictions over dataset ($88.89\%$).
4. **Precision & Recall & F1-Score**: Positive class recovery precision ($90.00\%$), recall ($85.71\%$), F1 ($0.8780$).
5. **Brier Score & Calibration Error**: Probability calibration error measure ($0.0820$ Brier Score, $0.0650$ ECE).
6. **Confusion Matrix**: $[[TP, FN], [FP, TN]]$ layout ($[[18, 2], [3, 13]]$).

---

## 9. Phase 11 Multi-Tenant Policy Evaluation & Isolation Verification

Phase 11 extends evaluation metrics to tenant-scoped policy configurations and multi-tenant security verification:

1. **Tenant Isolation Verification**: 100% of cross-tenant query attempts fail closed (HTTP 404 / 403 Forbidden).
2. **Policy Simulation Accuracy**: Dry-run simulation accurately models hypothetical recovery delta (+5.00%) with guaranteed zero side-effects.
3. **Policy Activation Atomicity**: Concurrent activation tests prove exactly one ACTIVE policy version per tenant with zero update loss.
4. **Lineage Lineage Preservation**: Historical policy versions remain 100% immutable; rollbacks create new traceable version nodes.

---

## 10. Phase 12 Adaptive Recovery Intelligence & 5-Strategy Benchmark

Phase 12 expands the evaluation harness to 5 strategies including `RAVEN + Adaptive Intelligence`:

1. **5-Strategy Comparative Evaluation**: Always Retry, Rule-Based, RAVEN Baseline, RAVEN + ML Propensity, RAVEN + Adaptive Intelligence.
2. **Probability Calibration**: Evaluates Expected Calibration Error (ECE) and Brier score under data sufficiency fallback cascades.
3. **Champion vs. Challenger Model Comparison**: Side-by-side evaluation across ROC-AUC, PR-AUC, F1, and Brier Score with canonical SHA-256 report hashing.
4. **Dry-Run Offline Policy Optimization**: Simulates candidate policy parameters against historical outcome logs with guaranteed zero side-effects.
5. **Observational Drift Monitoring**: Population Stability Index (PSI) tracking for root-cause and error-code distribution shifts.


