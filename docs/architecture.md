# RAVEN Architecture Specification

## 1. System Purpose

**RAVEN — Revenue-aware Autonomous Verification & ENgine** is an AI-powered revenue intelligence and autonomous recovery system built for payment processing ecosystems (specifically targeted at the Razorpay ecosystem under the AI Revenue Recovery track).

In payment processing systems, transaction failure rates, subscription drops, authorization timeouts, and asynchronous webhooks frequently create revenue leakage and revenue at risk. RAVEN ingests financial events, reconstructs true transaction and customer states from out-of-order and duplicated events, diagnoses failure root causes, plans bounded recovery interventions, enforces strict deterministic business policies, executes authorized recovery actions, and verifies true financial recovery with queryable decision traces.

---

## 2. Core Architectural Principles & Boundaries

1. **Event Log & Asynchronous Robustness**: Financial state is deterministically reconstructed from normalized financial events. Webhook arrival order must not be treated as financial event order.
2. **Deterministic vs. AI/ML Boundaries**: LLMs operate strictly within reasoning boundaries (root-cause diagnosis, evidence synthesis, candidate action generation, and reasoning explanations). LLMs never directly control monetary calculations, policy enforcement, authorization, or side-effects.
3. **Non-Bypassable Policy Engine**: Every autonomous action proposed by an agent must pass deterministic policy evaluation before execution. Policies hold absolute veto authority.
4. **Append-Only Audit Events & DecisionTrace**: Operations produce append-only audit events with controlled write access and integrity protections. A first-class `DecisionTrace` entity captures the complete lineage from event ingestion through policy approval to verification outcome.

---

## 3. Major Components & Responsibilities

```
[ External Webhook / Simulator Stream ]
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│              DETERMINISTIC INGESTION & STATE            │
│  - Event Ingestion & Deduplication (Idempotency Key)   │
│  - Normalized Event Log & State Reconstructor          │
│  - Revenue Risk Detector (Deterministic Rule Filters)   │
└─────────────────────────┬───────────────────────────────┘
                          │ Event Stream / Risk Trigger
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    AI / AGENT LAYER                     │
│  - Root Cause Analyst (Contextual Diagnosis)            │
│  - Recovery Planner (Candidate Action Generation)       │
│  - Verification Agent (Financial State Validation)      │
└─────────────────────────┬───────────────────────────────┘
                          │ Proposed Candidate Action + Confidence
                          ▼
┌─────────────────────────────────────────────────────────┐
│              DETERMINISTIC POLICY ENGINE                │
│  - Policy Verification (Limits, State Checks, Opt-out)  │
│  - Policy Decision: APPROVE / BLOCK / ESCALATE         │
└─────────────────────────┬───────────────────────────────┘
                          │ Ephemeral PolicyApprovalToken
                          ▼
┌─────────────────────────────────────────────────────────┐
│         SIDE-EFFECT EXECUTION & DECISION TRACE          │
│  - Tool Candidate Execution (Gateway / Communication)   │
│  - Append-Only Audit Event Logging & DecisionTrace      │
└─────────────────────────────────────────────────────────┘
```

---

## 4. End-to-End Decision Lifecycle

RAVEN provides complete queryable traceability across the decision lifecycle:

$$\text{EVENT} \rightarrow \text{STATE} \rightarrow \text{REVENUE RISK} \rightarrow \text{ROOT CAUSE} \rightarrow \text{CANDIDATE ACTIONS} \rightarrow \text{EXPECTED VALUE} \rightarrow \text{POLICY} \rightarrow \text{DECISION} \rightarrow \text{EXECUTION} \rightarrow \text{VERIFICATION} \rightarrow \text{OUTCOME}$$

This lifecycle is captured in the [`DecisionTrace`](file:///c:/Users/prana/Documents/RAVEN/docs/decision-trace.md) domain entity.

---

## 5. Candidate Tool Contracts & Domain Services

Capabilities in RAVEN are divided into **LLM-facing Candidate Tools** and **Internal Domain Services**. Agents interact only with candidate tools exposed via explicitly defined schemas. Side-effect tools require a valid `PolicyApprovalToken` to execute operations.

---

## 6. Integration vs. Simulation Boundaries

- **`simulator/`**: Local deterministic event producer generating complex edge cases (duplicate webhooks, out-of-order delivery, transient gateway timeouts, bank downtimes).
- **`apps/api/webhooks/`**: Production/Test mode webhook receiver that validates HMAC signatures against Razorpay headers (`X-Razorpay-Signature`).
- **`tools/`**: Unified adapter interface (`PaymentGatewayAdapter`). Routes to `SimulatorGatewayAdapter` in simulation mode and `RazorpayGatewayAdapter` in Razorpay mode.
