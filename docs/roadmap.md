# RAVEN Implementation Roadmap

## 1. Overview

This document outlines the phased development roadmap for **RAVEN**. Development proceeds in modular, independently testable phases. Speed must never be prioritized over financial correctness, test coverage, or architectural clarity.

---

## 2. Implementation Phases

### Phase 0: Engineering Foundation & Architecture Specification (COMPLETE)
- **Objective**: Establish repository structure, git configuration, environment discovery, and produce detailed architectural specifications.
- **Deliverables**:
  - Target directory structure (`apps/`, `agents/`, `domain/`, `ml/`, `tools/`, `policies/`, `events/`, `simulator/`, `data/`, `evaluation/`, `tests/`, `docs/`, `infra/`).
  - Core specification suite in `docs/` (`architecture.md`, `domain-model.md`, `event-architecture.md`, `agent-architecture.md`, `tool-architecture.md`, `policy-engine.md`, `evaluation.md`, `data-strategy.md`, `razorpay-integration.md`, `security.md`, `testing.md`, `roadmap.md`).
  - `.gitignore`, `.env.example`, `README.md`.
- **Acceptance Criteria**: All architecture documents written, reviewed, and validated against engineering quality rules.

---

### Phase 1: Core Domain, Event Sourcing & State Reconstruction Engine
- **Objective**: Implement core Pydantic domain models, immutable event ledger, deduplication logic, and deterministic event replay engine.
- **Deliverables**:
  - Domain models in `domain/` (`merchant.py`, `customer.py`, `order.py`, `payment.py`, `event.py`, `audit.py`).
  - Event Ingestion & Deduplication module in `events/ingestion.py`.
  - State Reconstruction Engine in `domain/state/reconstructor.py`.
- **Dependencies**: Phase 0.
- **Acceptance Criteria & Tests**: Unit tests in `tests/unit/` and `tests/events/` validating deduplication, sequence ordering, out-of-order handling, and late event state transitions.

---

### Phase 2: Synthetic Data Simulator & Ground Truth Generator
- **Objective**: Build deterministic synthetic event stream generator capable of emitting multi-scenario financial streams with embedded ground truth labels.
- **Deliverables**:
  - Synthetic Data Generator in `simulator/generator.py`.
  - Edge case scenario suites (Transient timeouts, hard declines, abandoned checkouts, duplicate webhooks, late authorizations).
  - Ground truth exporter saving reproducible datasets to `data/raw/`.
- **Dependencies**: Phase 1.
- **Acceptance Criteria & Tests**: Simulator successfully produces reproducible datasets across all 9 specified test scenarios with ground truth JSON output.

---

### Phase 3: Deterministic Policy Engine & Tool Infrastructure
- **Objective**: Implement non-bypassable policy engine rules (`POL_001` through `POL_007`), approval token generator, and 17 tool contracts.
- **Deliverables**:
  - Policy Engine module in `policies/engine.py`.
  - Policy Rules in `policies/rules.py`.
  - Tool contracts in `tools/` with permission checks and idempotency guards.
- **Dependencies**: Phase 1.
- **Acceptance Criteria & Tests**: Policy tests in `tests/policies/` confirming captured payment blocks, high-value escalations, max attempt caps, and unsigned tool execution rejections.

---

### Phase 4: Autonomous Agent Trio & LLM Reasoning Pipeline
- **Objective**: Build Root Cause Analyst, Recovery Planner, and Verification Agent modules.
- **Deliverables**:
  - Root Cause Analyst in `agents/root_cause/`.
  - Recovery Planner in `agents/recovery_planner/`.
  - Verification Agent in `agents/verifier/`.
  - Structured output schemas (Pydantic) and confidence evaluation logic.
- **Dependencies**: Phase 2, Phase 3.
- **Acceptance Criteria & Tests**: Contract tests verifying structured output formats, reasoning quality, and failure mode confidence scores.

---

### Phase 5: Evaluation Framework & Comparative Benchmark Suite
- **Objective**: Build automated benchmark framework evaluating RAVEN against 5 baseline strategies on reproducible synthetic datasets.
- **Deliverables**:
  - Benchmark CLI runner in `ml/evaluation/benchmark.py`.
  - Baseline runners (No recovery, Always retry, Rule-based recovery, ML-only, RAVEN).
  - Metrics exporter writing comparative tables to `evaluation/`.
- **Dependencies**: Phase 4.
- **Acceptance Criteria & Tests**: Benchmark CLI executes cleanly and generates reproducible comparative metrics across all 5 baselines without metric fabrication.

---

### Phase 6: Razorpay Integration Boundary & Webhook Receiver
- **Objective**: Implement production/test-mode HMAC signature verification, webhook endpoint, and Razorpay API adapter.
- **Deliverables**:
  - Webhook endpoint handler in `apps/api/webhooks/razorpay.py`.
  - Razorpay Gateway Adapter in `tools/razorpay_adapter.py`.
- **Dependencies**: Phase 3.
- **Acceptance Criteria & Tests**: Webhook signature verification tests passing for valid and invalid signatures.

---

### Phase 7: REST API & Operations Dashboard
- **Objective**: Expose management REST endpoints and build lightweight operations visualization dashboard.
- **Deliverables**:
  - FastAPI web server in `apps/api/`.
  - Operations dashboard in `apps/dashboard/` showing real-time risk queues, agent reasoning trails, policy blocks, and recovery metrics.
- **Dependencies**: Phase 5, Phase 6.
- **Acceptance Criteria & Tests**: End-to-end integration tests verifying web dashboard rendering and API response contracts.
