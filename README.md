# RAVEN — Revenue-aware Autonomous Verification & ENgine

> **Razorpay AI Buildathon — AI Revenue Recovery Track**  
> *Status: Architectural Specification & Foundation Phase (Under Active Development)*

## Overview

**RAVEN** (Revenue-aware Autonomous Verification & ENgine) is a prototype AI-powered revenue intelligence and autonomous recovery system designed for payment processing ecosystems. 

In digital payment systems, transaction failures, subscription drops, authorization timeouts, and asynchronous network errors frequently cause unrecovered revenue leakage. RAVEN provides an architectural framework to ingest financial events, reconstruct transaction state from out-of-order webhooks, diagnose failure root causes, plan bounded recovery interventions, enforce deterministic business policies, and verify financial outcomes.

---

## Architectural Principles

1. **Event Log & Asynchronous Robustness**: Financial state is deterministically reconstructed from normalized financial events. Webhook arrival order must not be treated as financial event order.
2. **Deterministic Financial Logic**: All monetary values are represented as integer minor units such as paise. Storage types will be selected during implementation based on domain constraints.
3. **AI Boundary Isolation & Safety**: AI agents operate within reasoning boundaries (root-cause diagnosis, evidence synthesis, candidate action generation). AI failures will never automatically result in an unsafe financial side effect.
4. **Non-Bypassable Policy Engine**: Every autonomous recovery action proposed by an agent must pass deterministic policy evaluation before execution. Policies hold absolute veto authority and issue signed `PolicyApprovalToken`s for approved side-effects.
5. **DecisionTrace & Append-Only Audit Events**: Operations produce append-only audit events with controlled write access and integrity protections. A first-class `DecisionTrace` domain entity captures the complete lineage from event ingestion through policy approval to verification outcome.
6. **Verifiable Evaluation**: System recovery performance is evaluated against seeded synthetic ground truth streams across 5 standardized baselines.

---

## High-Level System Architecture

```
[ Asynchronous Event Stream / Webhook ]
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│     1. Deterministic Ingestion & Event Deduplication    │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│     2. Event Log & State Reconstruction Engine          │
└─────────────────────────┬───────────────────────────────┘
                          │ Reconstructed State & Risk Triggers
                          ▼
┌─────────────────────────────────────────────────────────┐
│     3. Autonomous Agent Trio (Context & Planning)       │
│        - Root Cause Analyst Agent                       │
│        - Recovery Planner Agent                         │
│        - Verification Agent                             │
└─────────────────────────┬───────────────────────────────┘
                          │ Proposed Candidate Action
                          ▼
┌─────────────────────────────────────────────────────────┐
│     4. Deterministic Policy Engine (Absolute Veto)      │
└─────────────────────────┬───────────────────────────────┘
                          │ Ephemeral PolicyApprovalToken
                          ▼
┌─────────────────────────────────────────────────────────┐
│     5. Tool Candidates Execution & DecisionTrace Ledger │
└─────────────────────────────────────────────────────────┘
```

---

## System Documentation Index

The repository architecture and design specifications are documented in detail within the [`docs/`](file:///c:/Users/prana/Documents/RAVEN/docs) directory:

- [**Architecture Specification**](file:///c:/Users/prana/Documents/RAVEN/docs/architecture.md): Overall system structure, component boundaries, and data flow.
- [**Domain Model Specification**](file:///c:/Users/prana/Documents/RAVEN/docs/domain-model.md): Specifications for entities, fields, relationships, and invariants.
- [**DecisionTrace Specification**](file:///c:/Users/prana/Documents/RAVEN/docs/decision-trace.md): Complete lineage tracing from event ingestion to verification outcome.
- [**Event Architecture**](file:///c:/Users/prana/Documents/RAVEN/docs/event-architecture.md): Normalized event log, identity deduplication, and multi-factor state reconstruction.
- [**Agent Architecture**](file:///c:/Users/prana/Documents/RAVEN/docs/agent-architecture.md): Roles, contracts, tool candidates, failure modes, and safety fallbacks.
- [**Tool Architecture & Candidate Contracts**](file:///c:/Users/prana/Documents/RAVEN/docs/tool-architecture.md): Framing and contracts for candidate tools vs internal domain services.
- [**Policy Engine Specification**](file:///c:/Users/prana/Documents/RAVEN/docs/policy-engine.md): Deterministic rules, veto authority, and approval token security.
- [**AI Observability Specification**](file:///c:/Users/prana/Documents/RAVEN/docs/ai-observability.md): Telemetry, model versioning, latency, and PII masking.
- [**Code Quality Standards**](file:///c:/Users/prana/Documents/RAVEN/docs/code-quality.md): Python typing, Ruff linting, MyPy/Pyright static analysis, and test quality requirements.
- [**Evaluation Framework**](file:///c:/Users/prana/Documents/RAVEN/docs/evaluation.md): Quantitative metrics and comparative 5-baseline evaluation methodology.
- [**Data Strategy & Simulator**](file:///c:/Users/prana/Documents/RAVEN/docs/data-strategy.md): Synthetic stream generation, edge case scenarios, and ground truth schemas.
- [**Razorpay Integration Boundaries**](file:///c:/Users/prana/Documents/RAVEN/docs/razorpay-integration.md): Boundary definition between simulator and Razorpay test/live modes.
- [**Security & Compliance Model**](file:///c:/Users/prana/Documents/RAVEN/docs/security.md): Threat modeling, signature verification, RBAC, and PII masking.
- [**Testing Strategy**](file:///c:/Users/prana/Documents/RAVEN/docs/testing.md): Multi-tier test suite matrix and edge case assertion rules.
- [**Implementation Roadmap**](file:///c:/Users/prana/Documents/RAVEN/docs/roadmap.md): Phased deliverables, dependencies, and acceptance criteria.
- [**Architecture Decision Records (ADRs)**](file:///c:/Users/prana/Documents/RAVEN/docs/adr/):
  - [ADR-001: Deterministic Policy Engine Boundary](file:///c:/Users/prana/Documents/RAVEN/docs/adr/ADR-001-deterministic-policy-boundary.md)
  - [ADR-002: Financial State Reconstruction](file:///c:/Users/prana/Documents/RAVEN/docs/adr/ADR-002-financial-state-reconstruction.md)
  - [ADR-003: Agent Boundaries and Trio Isolation](file:///c:/Users/prana/Documents/RAVEN/docs/adr/ADR-003-agent-boundaries.md)
  - [ADR-004: Monetary Representation in Integer Minor Units](file:///c:/Users/prana/Documents/RAVEN/docs/adr/ADR-004-monetary-representation.md)
  - [ADR-005: LLM Provider Abstraction Layer](file:///c:/Users/prana/Documents/RAVEN/docs/adr/ADR-005-llm-provider-abstraction.md)

---

## Quick Start (Development Initialization)

### Environment Prerequisites
- Python `3.12+`
- Node.js `v26+` (npm `11+`)
- Git

### Setting Up Environment Variables
Copy `.env.example` to `.env` and fill in local testing parameters:
```bash
cp .env.example .env
```
*(Note: RAVEN uses placeholder environment variables only. Secrets must never be committed to source control.)*
