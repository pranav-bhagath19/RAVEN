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

---

### Phase 1: Core Domain, Event Processing & State Reconstruction Engine (COMPLETE)
- **Objective**: Implement core Pydantic domain models, minor unit currency validation, `DecisionTrace` model, append-only event log, deduplication logic, and state reconstructor.
- **Deliverables**:
  - Domain models in `domain/` (`merchant.py`, `customer.py`, `order.py`, `payment.py`, `event.py`, `decision_trace.py`, `audit.py`).
  - Event Ingestion & Identity Deduplication in `events/ingestion.py`.
  - Deterministic State Reconstructor in `domain/state/reconstructor.py`.

---

### Phase 2: Synthetic Data Simulator & Ground Truth Generator (COMPLETE)
- **Objective**: Build deterministic synthetic event stream generator capable of emitting multi-scenario financial streams with embedded ground truth labels.
- **Deliverables**:
  - Synthetic Data Generator in `simulator/generator.py`.
  - Edge case scenario suites (Transient timeouts, hard declines, abandoned checkouts, duplicate webhooks, late authorizations).
  - Ground truth exporter saving reproducible datasets to `data/raw/`.

---

### Phase 3: Deterministic Policy Engine & Tool Infrastructure (COMPLETE)
- **Objective**: Implement non-bypassable policy engine rules (`POL_001` through `POL_007`), approval token generator, tool candidates, and DecisionTrace execution hooks.
- **Deliverables**:
  - Policy Engine module in `policies/engine.py`.
  - Policy Rules in `policies/rules.py`.
  - HMAC-SHA256 `PolicyApprovalToken` in `policies/tokens.py`.
  - Tool candidate contracts in `tools/` with permission checks and idempotency guards.

---

### Phase 4: Autonomous Agent Trio & LLM Observability Pipeline (COMPLETE)
- **Objective**: Build Root Cause Analyst, Recovery Planner, and Verification Agent modules with explicit failure handling and AI observability logging.
- **Deliverables**:
  - Root Cause Analyst in `agents/root_cause/`.
  - Recovery Planner & Expected Value Calculator in `agents/recovery_planner/`.
  - Verification Agent in `agents/verifier/`.
  - LLM Provider Adapter and AI Observability Telemetry logger in `agents/observability.py`.
  - Top-Level Orchestrator in `agents/orchestrator.py`.

---

### Phase 5: Evaluation Framework & Comparative Benchmark Suite (COMPLETE)
- **Objective**: Build automated benchmark framework evaluating RAVEN against baseline strategies on reproducible synthetic datasets.
- **Deliverables**:
  - Benchmark CLI runner in `ml/evaluation/benchmark.py`.
  - Baseline runners (`Always Retry`, `Rule-Based Recovery`, `RAVEN`).
  - Metrics exporter writing comparative tables to `data/evaluation/benchmark_results_v1.json`.

---

### Phase 6: Razorpay Integration Boundary & Webhook Ingestion API Gateway (COMPLETE)
- **Objective**: Implement production/test-mode HMAC signature verification, webhook ingestion endpoint, canonical event mapping, and Razorpay API adapter boundary.
- **Deliverables**:
  - Webhook endpoint handler in `apps/api/routes/webhooks.py`.
  - FastAPI HTTP Gateway in `apps/api/main.py`.
  - Webhook Service & HMAC Signature Verification in `razorpay/signatures.py` and `apps/api/webhook_service.py`.
  - Razorpay Gateway Adapter & Mock Client in `razorpay/adapter.py` and `razorpay/client.py`.
  - Local CLI Demo Script in `apps/api/demo.py`.

---

### Phase 7: REST API & Operations Dashboard Control Plane (COMPLETE)
- **Objective**: Expose observational metrics, payment detail, DecisionTrace lineage, policy audit, telemetry, and controlled reprocessing commands over RAVEN engine.
- **Deliverables**:
  - Control plane schemas in `apps/api/operations_schemas.py`.
  - Repository query layer in `apps/api/repository.py`.
  - Operations application service in `apps/api/operations_service.py`.
  - Control plane REST router in `apps/api/routes/operations.py`.
  - Operational specification in `docs/operations-dashboard.md`.

---

### Phase 8: Production Deployment Prep & External Demo Polish (COMPLETE)
- **Objective**: Prepare RAVEN for production-style deployment, external technical demo, defensive security verification, and buildathon presentation.
- **Deliverables**:
  - Production Settings & Config in `apps/api/config.py`.
  - Structured Logging & Request Correlation Middleware in `apps/api/middleware.py`.
  - Global Exception Handlers in `apps/api/exceptions.py`.
  - Deterministic Demo Dataset in `data/demo/demo_scenarios.py`.
  - Interactive 15-Scenario CLI Demo in `scripts/demo.py`.
  - Defensive Security & Attack Vector Rejection Demo in `scripts/security_demo.py`.
  - Production Dockerfile & `.dockerignore`.
  - Comprehensive documentation in `README.md`, `docs/deployment.md`, and `docs/demo.md`.

---

### Phase 9: Production Persistence, Reliability & Live Integration (COMPLETE)
- **Objective**: Upgrade RAVEN with persistent PostgreSQL storage, Redis distributed idempotency, background recovery worker queues, live Razorpay API adapter, RBAC authentication, token-bucket rate limiting, and circuit breaker fault-tolerance.
- **Deliverables**:
  - Database connection & ORM models in `persistence/database.py` and `persistence/models.py`.
  - Repositories in `persistence/repositories/` (`payments`, `events`, `decisions`, `executions`, `verifications`, `telemetry`, `jobs`).
  - Distributed idempotency store in `persistence/redis_store.py`.
  - Background recovery worker daemon in `apps/worker/worker.py` and job queue in `persistence/queue.py`.
  - Live Razorpay HTTP gateway client in `razorpay/live_client.py`.
  - RBAC authorization module in `apps/api/auth.py`.
  - Rate limiting & circuit breaker fault-tolerance in `apps/api/rate_limiter.py` and `tools/circuit_breaker.py`.
  - Docker Compose production architecture in `docker-compose.yml`.

---

### Phase 10: Machine Learning Propensity Scoring & Adaptive Recovery Optimization (COMPLETE)
- **Objective**: Implement advisory ML propensity scoring layer predicting recovery probability $P(\text{success}) \in [0.0, 1.0]$ for candidate action ranking with deterministic EV calculation in integer minor units, target leakage prevention, artifact hash verification, 4-way comparative evaluation benchmark, and non-bypassable PolicyEngine veto protection.
- **Deliverables**:
  - Feature schema and leakage guard in `ml/features/schema.py`.
  - Feature pipeline transformation in `ml/features/pipeline.py`.
  - Dataset builder and chronological partitioning in `ml/dataset.py`.
  - Logistic Regression Propensity Model in `ml/models/propensity.py`.
  - Artifact manager & SHA-256 hashing in `ml/models/artifact.py`.
  - RecoveryPlanner ML integration & fallback in `agents/recovery_planner/planner.py`.
  - ML metrics & 4-strategy benchmark harness in `ml/evaluation/metrics.py`, `strategies.py`, `runner.py`.
  - Control plane ML REST endpoints in `apps/api/routes/operations.py`.
  - Interactive Phase 10 demonstration in `scripts/phase10_demo.py`.
  - Comprehensive documentation in `docs/phase10.md`.

---


---

### Phase 12: Adaptive Recovery Intelligence & Offline Policy Optimization (COMPLETE)
- **Objective**: Extend RAVEN from static advisory propensity scoring into a deterministic, offline-trained adaptive recovery intelligence system supporting empirical action statistics, tenant recovery profiles, calibrated adaptive probability scoring, observational drift detection, dry-run offline policy optimization, counterfactual scenario evaluation, model registry champion/challenger workflows, 5-strategy comparative benchmark, and read-only REST intelligence APIs while maintaining non-negotiable security boundaries.
- **Deliverables**:
  - Dataset builder and target leakage guard in `ml/adaptive/dataset.py`.
  - Action-level empirical statistics analyzer in `ml/adaptive/action_statistics.py`.
  - Tenant recovery intelligence profiles in `ml/adaptive/tenant_intelligence.py`.
  - Calibrated adaptive recovery scorer in `ml/adaptive/scorer.py`.
  - Calibration analyzer in `ml/adaptive/calibration.py`.
  - Observational drift detector in `ml/adaptive/drift.py`.
  - Offline dry-run policy optimizer in `ml/optimization/policy_optimizer.py`.
  - Counterfactual evaluator in `ml/optimization/counterfactual.py`.
  - Model registry & champion/challenger evaluator in `ml/models/registry.py` and `ml/evaluation/champion_challenger.py`.
  - RecoveryPlanner integration in `agents/recovery_planner/planner.py`.
  - Operations Intelligence REST endpoints in `apps/api/routes/intelligence.py`.
  - 5-strategy evaluation benchmark in `ml/evaluation/runner.py`.
  - Interactive Phase 12 demonstration in `scripts/phase12_demo.py`.
  - Comprehensive documentation in `docs/phase12.md`.


