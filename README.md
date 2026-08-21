# RAVEN — Revenue-aware Autonomous Verification & ENgine

> **Razorpay AI Buildathon — AI Revenue Recovery Track**  
> *Status: Architectural Specification & Foundation Phase (Under Active Development)*

## Overview

**RAVEN** (Revenue-aware Autonomous Verification & ENgine) is a prototype AI-powered revenue intelligence and autonomous recovery system designed for payment processing ecosystems. 

In digital payment systems, transaction failures, subscription drops, authorization timeouts, and asynchronous network errors frequently cause unrecovered revenue leakage. RAVEN provides an architectural framework to ingest financial events, reconstruct transaction state from out-of-order webhooks, diagnose failure root causes, plan bounded recovery interventions, enforce deterministic business policies, and verify financial outcomes.

---

## Architectural Principles

1. **Deterministic Financial Logic**: All monetary values are processed strictly in integer minor units (`paise`). Financial math and state machines are 100% deterministic.
2. **AI Boundary Isolation**: AI agents generate contextual diagnoses and candidate recovery plans, but have zero authority to execute side-effects or override business rules directly.
3. **Non-Bypassable Policy Engine**: Every autonomous recovery action must pass deterministic policy checks before execution. Policies hold absolute veto power.
4. **Asynchronous Robustness**: Event processing engine is designed for out-of-order, delayed, and duplicated webhooks via state replay and cryptographic deduplication.
5. **Verifiable Evaluation**: System recovery performance is evaluated against seeded synthetic ground truth streams across 5 standardized baselines.

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
│     2. Event Sourcing & State Reconstruction Engine     │
└─────────────────────────┬───────────────────────────────┘
                          │ State & Risk Flag
                          ▼
┌─────────────────────────────────────────────────────────┐
│     3. Autonomous Agent Trio (Context & Planning)       │
│        - Root Cause Analyst Agent                       │
│        - Recovery Planner Agent                         │
│        - Verification Agent                             │
└─────────────────────────┬───────────────────────────────┘
                          │ Proposed Recovery Action
                          ▼
┌─────────────────────────────────────────────────────────┐
│     4. Deterministic Policy Engine (Absolute Veto)      │
└─────────────────────────┬───────────────────────────────┘
                          │ Approved Token Only
                          ▼
┌─────────────────────────────────────────────────────────┐
│     5. Tool Execution & Immutable Audit Ledger          │
└─────────────────────────────────────────────────────────┘
```

---

## System Documentation Index

The repository architecture and design specifications are documented in detail within the [`docs/`](file:///c:/Users/prana/Documents/RAVEN/docs) directory:

- [**Architecture Specification**](file:///c:/Users/prana/Documents/RAVEN/docs/architecture.md): Overall system structure, component boundaries, and data flow.
- [**Domain Model Specification**](file:///c:/Users/prana/Documents/RAVEN/docs/domain-model.md): Specifications for entities, fields, relationships, and invariants.
- [**Event Architecture**](file:///c:/Users/prana/Documents/RAVEN/docs/event-architecture.md): Webhook ingestion, cryptographic deduplication, and event replay state reconstruction.
- [**Agent Architecture**](file:///c:/Users/prana/Documents/RAVEN/docs/agent-architecture.md): Roles, contracts, tools, constraints, and escalation behavior for the 3 agents.
- [**Tool Architecture**](file:///c:/Users/prana/Documents/RAVEN/docs/tool-architecture.md): Contracts for all 17 system and side-effect tools.
- [**Policy Engine Specification**](file:///c:/Users/prana/Documents/RAVEN/docs/policy-engine.md): Deterministic rules, veto authority, and approval token security.
- [**Evaluation Framework**](file:///c:/Users/prana/Documents/RAVEN/docs/evaluation.md): Quantitative metrics and comparative 5-baseline evaluation methodology.
- [**Data Strategy & Simulator**](file:///c:/Users/prana/Documents/RAVEN/docs/data-strategy.md): Synthetic stream generation, edge case scenarios, and ground truth schemas.
- [**Razorpay Integration Boundaries**](file:///c:/Users/prana/Documents/RAVEN/docs/razorpay-integration.md): Boundary definition between simulator and Razorpay test/live modes.
- [**Security & Compliance Model**](file:///c:/Users/prana/Documents/RAVEN/docs/security.md): Threat modeling, signature verification, RBAC, and PII masking.
- [**Testing Strategy**](file:///c:/Users/prana/Documents/RAVEN/docs/testing.md): Multi-tier test suite matrix and edge case assertion rules.
- [**Implementation Roadmap**](file:///c:/Users/prana/Documents/RAVEN/docs/roadmap.md): Phased deliverables, dependencies, and acceptance criteria.

---

## Repository Structure

```text
raven/
├── apps/               # API server & dashboard frontend
├── agents/             # Root Cause, Recovery Planner, and Verifier agents
├── domain/             # Entities, payment models, state reconstruction
├── ml/                 # Feature extraction, models, evaluation scripts
├── tools/              # Unified tool contracts & gateway adapters
├── policies/           # Deterministic policy rules & token engine
├── events/             # Webhook ingestion, normalization, deduplication
├── simulator/          # Synthetic event generator & ground truth streams
├── data/               # Raw & processed synthetic evaluation datasets
├── evaluation/         # Benchmark results & comparison metrics
├── tests/              # Multi-tier pytest suite
├── docs/               # Comprehensive architecture specifications
└── infra/              # Deployment & environment configurations
```

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
