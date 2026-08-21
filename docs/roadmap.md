# RAVEN Implementation Roadmap

## 1. Overview

This document outlines the phased development roadmap for **RAVEN**. Development proceeds in modular, independently testable phases. Speed must never be prioritized over financial correctness, test coverage, code quality, or architectural clarity.

---

## 2. Implementation Phases

### Phase 0: Engineering Foundation & Architecture Specification (COMPLETE)
- **Objective**: Establish repository structure, git configuration, environment discovery, and produce revised architectural specifications.
- **Deliverables**:
  - Target directory structure (`apps/`, `agents/`, `domain/`, `ml/`, `tools/`, `policies/`, `events/`, `simulator/`, `data/`, `evaluation/`, `tests/`, `docs/`, `infra/`).
  - Architecture specifications in `docs/` (`architecture.md`, `domain-model.md`, `event-architecture.md`, `agent-architecture.md`, `tool-architecture.md`, `policy-engine.md`, `evaluation.md`, `data-strategy.md`, `razorpay-integration.md`, `security.md`, `testing.md`, `roadmap.md`, `decision-trace.md`, `ai-observability.md`, `code-quality.md`).
  - Architecture Decision Records in `docs/adr/` (`ADR-001` through `ADR-005`).
  - `.gitignore`, `.env.example`, `README.md`.
- **Acceptance Criteria**: All architectural corrections verified (Event Log terminology, non-timestamp state reconciliation, flexible integer minor units, DecisionTrace domain model, AI failure modes, AI observability, ADRs, and code-quality standards).

---

### Phase 1: Core Domain, Event Processing & State Reconstruction Engine
- **Objective**: Implement core Pydantic domain models, minor unit currency validation, `DecisionTrace` model, append-only event log, deduplication logic, and state reconstructor.
- **Deliverables**:
  - Domain models in `domain/` (`merchant.py`, `customer.py`, `order.py`, `payment.py`, `event.py`, `decision_trace.py`, `audit.py`).
  - Event Ingestion & Identity Deduplication in `events/ingestion.py`.
  - Deterministic State Reconstructor in `domain/state/reconstructor.py`.
- **Dependencies**: Phase 0.
- **Acceptance Criteria & Tests**: Pytest suite in `tests/events/` validating deduplication, sequence ordering, out-of-order state resolution, and late event reconciliation.

---

### Phase 2: Synthetic Data Simulator & Ground Truth Generator
- **Objective**: Build deterministic synthetic event stream generator capable of emitting multi-scenario financial streams with embedded ground truth labels.
- **Deliverables**:
  - Synthetic Data Generator in `simulator/generator.py`.
  - Edge case scenario suites (Transient timeouts, hard declines, abandoned checkouts, duplicate webhooks, late authorizations).
  - Ground truth exporter saving reproducible datasets to `data/raw/`.
- **Dependencies**: Phase 1.

---

### Phase 3: Deterministic Policy Engine & Tool Infrastructure
- **Objective**: Implement non-bypassable policy engine rules (`POL_001` through `POL_007`), approval token generator, tool candidates, and DecisionTrace execution hooks.
- **Deliverables**:
  - Policy Engine module in `policies/engine.py`.
  - Policy Rules in `policies/rules.py`.
  - Tool candidate contracts in `tools/` with permission checks and idempotency guards.
- **Dependencies**: Phase 1.

---

### Phase 4: Autonomous Agent Trio & LLM Observability Pipeline
- **Objective**: Build Root Cause Analyst, Recovery Planner, and Verification Agent modules with explicit failure handling and AI observability logging.
- **Deliverables**:
  - Root Cause Analyst in `agents/root_cause/`.
  - Recovery Planner in `agents/recovery_planner/`.
  - Verification Agent in `agents/verifier/`.
  - LLM Provider Adapter and AI Observability Telemetry logger in `agents/observability.py`.
- **Dependencies**: Phase 2, Phase 3.

---

### Phase 5: Evaluation Framework & Comparative Benchmark Suite
- **Objective**: Build automated benchmark framework evaluating RAVEN against 5 baseline strategies on reproducible synthetic datasets.
- **Deliverables**:
  - Benchmark CLI runner in `ml/evaluation/benchmark.py`.
  - Baseline runners (No recovery, Always retry, Rule-based recovery, ML-only, RAVEN).
  - Metrics exporter writing comparative tables to `evaluation/`.
- **Dependencies**: Phase 4.

---

### Phase 6: Razorpay Integration Boundary & Webhook Receiver
- **Objective**: Implement production/test-mode HMAC signature verification, webhook endpoint, and Razorpay API adapter.
- **Deliverables**:
  - Webhook endpoint handler in `apps/api/webhooks/razorpay.py`.
  - Razorpay Gateway Adapter in `tools/razorpay_adapter.py`.
- **Dependencies**: Phase 3.

---

### Phase 7: REST API & Operations Dashboard
- **Objective**: Expose management REST endpoints and build operations visualization dashboard for DecisionTrace inspection.
- **Deliverables**:
  - FastAPI web server in `apps/api/`.
  - Operations dashboard in `apps/dashboard/` rendering real-time risk queues, `DecisionTrace` graphs, policy block logs, and recovery metrics.
- **Dependencies**: Phase 5, Phase 6.
