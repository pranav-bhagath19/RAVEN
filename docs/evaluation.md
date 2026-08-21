# RAVEN Evaluation Framework & Baseline Benchmarks

## 1. Evaluation Philosophy & Rules

Evaluation of RAVEN must be strictly empirical, objective, and reproducible. 

### Mandate against Metric Fabrication
- **No Invented Metrics**: All reported metrics in documentation, logs, or reports must originate from executed synthetic simulator runs or benchmark test suites.
- **Reproducible Seeded Experiments**: Simulator runs must use fixed pseudo-random seeds to ensure 100% reproducible results.

---

## 2. Quantitative Evaluation Metrics

### 2.1 State Reconstruction Metrics
Evaluates the core Event Replay Engine's ability to reconstruct ground truth state from noisy event streams.

- **State Reconstruction Accuracy (\(S_{acc}\))**:
  $$S_{acc} = \frac{\text{Correct Reconstructed Entity States}}{\text{Total Synthetic Entities}} \times 100$$
- **Duplicate Event Resilience Rate**: Percentage of duplicated webhooks correctly identified and deduped without corrupting state.
- **Out-of-Order Handling Success Rate**: Percentage of out-of-order webhook sequences where the final derived state equals ground truth state.
- **Ambiguity Detection Rate**: Percentage of unresolvable/stalled payments correctly classified as `AMBIGUOUS`.

---

### 2.2 Revenue Risk Detection Metrics
Evaluates the identification of recoverable revenue opportunities versus unrecoverable failures (e.g. hard card declines).

- **Precision (\(P_{risk}\))**:
  $$P_{risk} = \frac{\text{True Positive Recoverable Risks Flagged}}{\text{Total Risks Flagged by RAVEN}}$$
- **Recall (\(R_{risk}\))**:
  $$R_{risk} = \frac{\text{True Positive Recoverable Risks Flagged}}{\text{Total Ground Truth Recoverable Risks}}$$
- **False Positive Rate (\(FPR_{risk}\))**: Ratio of unrecoverable/hard-failed transactions incorrectly flagged as recoverable opportunities.

---

### 2.3 Recovery Performance Metrics
Evaluates actual financial recovery and intervention efficiency.

- **Recovery Rate (\(RR\))**:
  $$RR = \frac{\text{Successfully Recovered Transactions}}{\text{Total Revenue-at-Risk Opportunities}} \times 100$$
- **Net Recovered Revenue (\(NRR\))**: Total value of recovered funds minus total intervention operational costs:
  $$NRR = \sum \text{Recovered Amount (paise)} - \sum \text{Intervention Costs (paise)}$$
- **Unnecessary Intervention Rate**: Percentage of transactions where an intervention was dispatched but customer would have naturally retried/paid organically without assistance.
- **Intervention Success Rate**: Percentage of executed recovery actions that directly resulted in captured payment.

---

### 2.4 Agent & Policy Metrics
Evaluates agent reasoning quality, tool execution safety, and policy compliance.

- **Tool Selection Accuracy**: Percentage of agent steps where appropriate, minimal tools were called.
- **Policy Compliance Rate**: Must be strictly **100.0%**. Percentage of executed side-effect actions that held valid policy tokens.
- **Reasoning Correctness Score**: Human/LLM-as-a-judge score evaluating alignment between actual root cause logs and agent explanation.

---

### 2.5 Operational & Escalation Metrics
- **p50 / p95 / p99 Ingestion-to-Action Latency**: Time elapsed from webhook ingestion to policy decision.
- **Human Escalation Rate**: Percentage of total opportunities routed to human operators.
- **System Failure Rate**: Unhandled exception rate across ingestion and execution pipelines.

---

## 3. Comparative Baseline Framework

RAVEN will be evaluated against **5 standardized baseline strategies** operating on identical synthetic dataset runs:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        EVALUATION DATASET                              │
│         Synthetic Simulator Stream (Seeded Ground Truth)               │
└────────────────────────────────────────────────────────────────────────┘
                                    │
    ┌──────────────┬────────────────┼────────────────┬────────────────┐
    ▼              ▼                ▼                ▼                ▼
┌─────────┐  ┌───────────┐  ┌───────────────┐  ┌───────────┐  ┌───────────────┐
│Baseline1│  │Baseline 2 │  │  Baseline 3   │  │Baseline 4 │  │  Baseline 5   │
│   No    │  │  Always   │  │  Rule-Based   │  │  ML-Only  │  │     RAVEN     │
│Recovery │  │   Retry   │  │   Recovery    │  │ (No Policy│  │(Full System)  │
│         │  │           │  │ (Fixed Rules) │  │  Engine)  │  │               │
└─────────┘  └───────────┘  └───────────────┘  └───────────┘  └───────────────┘
```

1. **Baseline 1: No Recovery (Control)**: Standard passive baseline. Zero recovery interventions performed. Measures natural organic customer retry rate.
2. **Baseline 2: Always Retry**: Naive automated strategy. Retries every failed payment exactly 3 times at fixed 5-minute intervals, ignoring error codes, bank downtimes, or card decline types.
3. **Baseline 3: Rule-Based Recovery**: Deterministic heuristic rules (e.g. retry transient errors once after 10 mins; send SMS for abandoned checkouts after 1 hr). No AI reasoning or context synthesis.
4. **Baseline 4: ML-Only Strategy**: Direct LLM/ML agent recommendation driving execution directly, **without** the Deterministic Policy Engine or Event Replay state reconstructor.
5. **Baseline 5: RAVEN (Full System)**: Event Replay State Reconstructor + Agent Trio + Deterministic Policy Engine + Audit System.

---

## 4. Benchmark Execution Command Specification

Evaluation experiments will be executed via standard CLI commands:
```bash
python -m ml.evaluation.benchmark --dataset data/raw/simulated_dataset_v1.json --seed 42 --baselines 1,2,3,4,5 --output evaluation/results_v1.json
```
Results will generate reproducible comparison tables printed to console and stored in `evaluation/`.
