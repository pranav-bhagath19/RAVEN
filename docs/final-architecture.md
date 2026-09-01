# RAVEN Final System Architecture Specification

## 1. Executive Summary

RAVEN is an autonomous, multi-tenant payment recovery engine designed to orchestrate automated recovery workflows for failed financial transactions. The system combines advisory LLM/ML intelligence layers with deterministic, non-bypassable policy enforcement and cryptographic tool execution boundaries.

---

## 2. End-to-End Pipeline & Trust Boundaries

```
                 [ Webhook / Event Ingestion ]
                               │
                ( Event Deduplication Engine )
                               │
               [ State Reconstructor & Database ]
                               │
              ( Root Cause Analysis Agent / LLM )
                               │
             ( ML / Adaptive / Bandit Intelligence )
                    [ Advisory Recommendations ]
                               │
                               ▼
                    ┌─────────────────────┐
                    │    PolicyEngine     │  ◄── [ Merchant Policy Rules ]
                    │   (Veto Authority)  │
                    └──────────┬──────────┘
                               │
                     [ APPROVED / BLOCKED ]
                               │
                ┌──────────────┴──────────────┐
                │                             │
          ( BLOCKED )                   ( APPROVED )
                │                             │
                ▼                             ▼
       [ Abort Execution ]           [ HMAC-SHA256 Token ]
                                              │
                                              ▼
                                    ┌──────────────────┐
                                    │   ToolExecutor   │  ◄── (Execution Boundary)
                                    └─────────┬────────┘
                                              │
                                    [ Dispatch Tool ]
                                              │
                                              ▼
                                   [ VerificationAgent ]
                                              │
                                              ▼
                                    [ DecisionTrace Log ]
```

---

## 3. Core Architectural Subsystems

### 1. Ingestion & State Reconstruction
- Webhooks pass constant-time HMAC signature checks.
- Event deduplication prevents processing duplicate payment notifications.
- `StateReconstructor` builds an immutable input state snapshot from financial event streams.

### 2. Advisory Intelligence Trio
- **Root Cause Analyst**: Identifies failure vectors (e.g. gateway timeouts, insufficient funds).
- **ML Propensity & Adaptive Scorer**: Predicts probability of recovery `P(success | state, action)`.
- **LinUCB Contextual Bandit**: Ranks approved recovery actions using upper confidence bound exploration.
- **Invariant**: All ML/LLM/Bandit outputs are strictly advisory.

### 3. Deterministic Policy Enforcement
- `PolicyEngine` enforces rules `POL_001` through `POL_007`.
- Evaluates merchant policy overrides, retry budgets, quiet periods, and currency limits.
- Supremacy: Returns `APPROVED` or `BLOCKED`. A `BLOCKED` decision halts processing immediately.

### 4. Cryptographic Tool Execution
- `generate_approval_token` issues an HMAC-SHA256 token encoding decision and payment bindings.
- `ToolExecutor` verifies token validity, signature, expiration (300s TTL), and idempotency key before dispatch.

### 5. Telemetry & Telemetry Trace Correlation
- Every decision captures full audit lineage in `DecisionTrace`.
- Tracked attributes: `decision_id`, `tenant_id`, `policy_id`, `policy_version`, `policy_hash`, `execution_result`, `verification_result`.

---

## 4. Multi-Region Reliability & Replication

- Multi-region policy configuration hashing via `compute_policy_hash`.
- `PolicyReplicator` syncs merchant policies between primary and secondary regions.
- `PolicyConflictDetector` and `PolicyReconciler` resolve divergent branches via version-tree lineage evaluation.
- `RegionalFailoverManager` routes requests dynamically and enforces fail-closed behavior on stale reads (>300s).
