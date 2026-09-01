# RAVEN Phase 13 Architecture & Implementation
## Bounded Contextual Bandit Recovery Optimization

### Executive Summary

Phase 13 extends RAVEN's recovery optimization stack from static ML propensity scoring and empirical tenant adaptive scoring into a **Safe, Bounded Contextual Bandit decision-optimization layer**. Using a linear Upper Confidence Bound (**LinUCB**) algorithm, Phase 13 learns which recovery intervention is optimal for specific contextual failure scenarios while strictly enforcing every deterministic safety boundary.

### Architectural Invariants

1. **Advisory-Only Authority**: The Contextual Bandit ranks candidate actions proposed by the `RecoveryPlanner`. It possesses **zero side-effect tool execution authority**, **zero token minting authority**, and **zero policy modification authority**.
2. **PolicyEngine Absolute Veto**: `PolicyEngine` remains the supreme veto authority (`POL_001`–`POL_007`). Even if a candidate action achieves a maximum bandit UCB score or predicted success probability \( P = 0.99 \), if `PolicyEngine` evaluates the action as `BLOCKED`, no `PolicyApprovalToken` is issued and `ToolExecutor` refuses execution.
3. **Pre-Action Context Leakage Guard**: The 12-dimensional context vector is built strictly from pre-action features. Any attempt to include post-action outcome fields (`recovered_amount_minor`, `is_recovered`, `verification_status`, `executed_at`, `tool_result`) immediately triggers a `ValueError`.
4. **Strict Tenant Isolation**: Contextual Bandit models and statistics maintain strict `tenant_id` scoping to prevent cross-tenant data contamination.
5. **Deterministic Fallback Cascade**: Unseen tenants or corrupted model states cascade safely: `CONTEXTUAL_BANDIT -> GLOBAL_CONTEXTUAL_BANDIT -> ADAPTIVE_PROPENSITY -> BASE_PROPENSITY -> DETERMINISTIC_FALLBACK`.

---

### Context Vector Schema (12 Dimensions)

| Dimension | Feature Name | Description |
|---|---|---|
| 0 | `amount_scaled` | Payment amount in INR scaled by 1,000,000 |
| 1 | `attempts_count` | Previous failure attempt count |
| 2 | `currency_code_encoded` | Encoded currency (1.0 for INR) |
| 3 | `error_code_encoded` | Encoded failure error code |
| 4 | `root_cause_encoded` | Encoded failure root cause |
| 5 | `action_type_encoded` | Encoded candidate action type |
| 6 | `merchant_status_encoded` | Merchant account status (1.0 for ACTIVE) |
| 7 | `customer_opt_out_flag` | Customer opt-out flag (0.0 or 1.0) |
| 8 | `systemic_downtime_flag` | Systemic bank downtime indicator |
| 9 | `base_propensity` | Base ML propensity score |
| 10 | `tenant_action_success_rate` | Empirical tenant action success rate |
| 11 | `global_action_success_rate` | Empirical global action success rate |

---

### LinUCB Mathematics

For each candidate action \( a \in \mathcal{A} \) given context vector \( \mathbf{x} \in \mathbb{R}^{12} \):

\[
\text{UCB}(a \mid \mathbf{x}) = \boldsymbol{\theta}_a^\top \mathbf{x} + \alpha \sqrt{\mathbf{x}^\top \mathbf{A}_a^{-1} \mathbf{x}}
\]

where:
- \( \mathbf{A}_a = \mathbf{I}_{12} + \sum_{\tau} \mathbf{x}_\tau \mathbf{x}_\tau^\top \)
- \( \mathbf{b}_a = \sum_{\tau} r_\tau \mathbf{x}_\tau \)
- \( \boldsymbol{\theta}_a = \mathbf{A}_a^{-1} \mathbf{b}_a \)
- \( \alpha \in [0.01, 2.0] \) is the exploration upper confidence bound coefficient.

---

### API Endpoints

- `GET /api/v1/operations/intelligence/bandit`
- `GET /api/v1/operations/intelligence/bandit/actions`
- `GET /api/v1/operations/intelligence/bandit/tenants/{tenant_id}`
- `GET /api/v1/operations/intelligence/bandit/evaluation`
- `GET /api/v1/operations/intelligence/bandit/models`
- `GET /api/v1/operations/intelligence/bandit/models/{model_version}`
- `POST /api/v1/operations/intelligence/bandit/simulate` (Dry-run mode only)

---

### Verification & Quality Gates

- Pytest: 225/225 tests passing
- Ruff: 0 errors
- MyPy: 0 errors across 215 source files
- Phase 12 Demo: Exit code 0
- Phase 13 Demo: Exit code 0
