# RAVEN — Razorpay AI Buildathon Track 03 Submission Guide

## Autonomous Revenue Recovery & Verification Engine

**Track**: Track 03 — AI Revenue Recovery  
**Target Platform**: Razorpay Payment Gateway Integration  
**Architecture Status**: **Phases 1–15 Productionized & Certified**  
**Test Coverage**: **268/268 Pytest Cases Passed (100% Green)**  
**Certification Harness**: **15/15 Phase 15 Scenarios Passed (`python scripts/phase15_certification.py`)**  

---

## Executive Overview
RAVEN is a revenue-aware autonomous verification and engine built specifically for merchants on Razorpay. It ingests failed Razorpay payment webhooks, reconstructs real-time transaction state, performs LLM/heuristic root cause analysis, ranks recovery options via LinUCB contextual bandits & ML propensity models, enforces non-bypassable deterministic merchant policies, and executes cryptographically signed recovery actions via WhatsApp, SMS, and Email.

---

## Key Features & Highlights

### 1. Webhook Ingestion & State Reconstruction
- Ingests raw Razorpay `payment.failed` webhooks via `POST /api/v1/webhooks/razorpay`.
- Verifies constant-time HMAC-SHA256 request signatures against `RAZORPAY_WEBHOOK_SECRET`.
- Reconstructs append-only financial event ledgers while guaranteeing idempotency via SHA-256 content deduplication.

### 2. Autonomous Agent Trio Pipeline
- **RootCauseAnalyst**: Diagnoses underlying card issuer declines, insufficient funds, network timeouts, and authentication drop-offs (OpenAI GPT-4o with deterministic rule fallbacks).
- **RecoveryPlanner**: Evaluates candidate recovery strategies (Smart Retry, Payment Link Dispatch, Fallback Channel Notification, Merchant Human Escalation) using LinUCB contextual bandits.
- **VerificationAgent**: Verifies recovery outcomes and measures exact salvaged revenue in integer minor units (paise).

### 3. Non-Negotiable Financial & Security Guardrails
- **ML & LLM Advisory-Only**: Machine learning models and LLMs recommend candidate actions; they hold **ZERO** execution authority.
- **PolicyEngine Veto Protection**: Merchant-defined rules (`POL_001` - `POL_007`) evaluate candidates. If vetoed (`BLOCKED`), execution is stopped immediately.
- **HMAC-SHA256 PolicyApprovalToken**: Executions require a secret-signed 5-minute approval token issued exclusively by the policy authorization boundary.
- **ToolExecutor Boundary**: `ToolExecutor` is the sole side-effect boundary. It verifies token signatures, idempotency locks, and action parameters prior to dispatching external calls.
- **Integer Minor-Unit Math**: All financial amounts are calculated and stored strictly in integer minor units (paise/cents), eliminating floating-point rounding errors.

### 4. Live Next.js Operations Dashboard ([`apps/dashboard`](file:///c:/Users/prana/Documents/RAVEN/apps/dashboard))
- 21 production routes providing complete operational visibility:
  - Real-time revenue recovery metrics & salvaged INR counters.
  - Interactive DecisionTrace timeline viewer for every transaction.
  - Policy Engine ruleset configuration manager, version history graph, counterfactual simulator, and audit trail.
  - LinUCB bandit exploration vs exploitation metrics and feature drift observability.

---

## Quickstart Guide for Judges

### 1. Run Complete 15-Scenario Certification Suite
```bash
python scripts/phase15_certification.py
```

### 2. Run Interactive Live Demo Harness
```bash
python scripts/live_buildathon_demo.py
```

### 3. Run Backend API Server & Expose Webhook Tunnel
```bash
# Terminal 1: Run FastAPI Gateway Server
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Expose Public HTTPS Webhook Tunnel via Python SDK
python scripts/start_ngrok_tunnel.py
```
Swagger API Documentation will be accessible at: `http://localhost:8000/docs`

### 4. Run Next.js Frontend Dashboard
```bash
cd apps/dashboard
npm run dev
```
Dashboard UI will be accessible at: `http://localhost:3000`

### 5. Run Full Docker Stack
```bash
docker compose up --build -d
```

---

## Test Verification Summary
- **Pytest Unit & Integration**: `pytest` → **268 / 268 Passed**
- **Ruff Linter**: `ruff check .` → **All checks passed!**
- **MyPy Type Checker**: `mypy ...` → **Success: no issues found in 246 source files**
- **Alembic Database**: `alembic upgrade head` → **Applied `3a3310de7765_initial_schema`**
- **Next.js Dashboard**: `npm run build` → **Compiled all 21 static & dynamic routes**
