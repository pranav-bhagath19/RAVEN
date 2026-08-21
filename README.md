# RAVEN — Revenue-aware Autonomous Verification & ENgine

**RAVEN** is a production-shaped, zero-trust autonomous revenue recovery engine built for payment gateways, merchants, and financial infrastructure. Developed for the **Razorpay AI Buildathon** under the **AI Revenue Recovery** track.

---

## 1. The Problem

Payment failures (transient gateway timeouts, network drops, issuer downtime, card limits) cause massive revenue leakage for merchants. Naive automated retries or unconstrained AI agents introduce severe financial & operational risks:

- **Duplicate Charges**: Retrying payments without terminal state verification.
- **Communication Spam**: Repeated customer alerts causing opt-out violations.
- **Outage Flooding**: Retrying transactions during systemic bank outages.
- **Misattribution**: Claiming credit for organic customer retries.
- **Dangerous Unconstrained AI**: Giving LLMs direct side-effect authority over real money.

---

## 2. The Solution: Architectural Isolation

RAVEN strictly separates **AI Reasoning** from **Deterministic Financial Authority**:

```
Razorpay Webhook (HTTP POST)
        │
        ▼
Signature Verification (HMAC-SHA256)
        │
        ▼
Event Ingestion + Content Hash Deduplication
        │
        ▼
State Reconstruction Engine (Non-timestamp Sequence Tie-Breaking)
        │
        ▼
Root Cause Analyst (LLM / Deterministic Heuristic Fallback)
        │
        ▼
Recovery Planner & Deterministic Expected Value Calculator
        │
        ▼
Deterministic Policy Engine (Non-bypassable Veto Authority)
        │
        ▼
HMAC-SHA256 PolicyApprovalToken Issuance
        │
        ▼
ToolExecutor (Sole Execution Boundary Requiring Valid Token)
        │
        ▼
Deterministic Verification Agent (Attribution Precision)
        │
        ▼
DecisionTrace Lineage Logging ──► Operations Control Plane Dashboard
```

---

## 3. Key Invariants & Safeguards

1. **Zero LLM Authority**: LLMs only produce structured candidate proposals; they **NEVER** hold side-effect authority or issue authorization tokens.
2. **Deterministic Policy Engine**: Policies (`POL_001` through `POL_007`) enforce non-bypassable guardrails (terminal payment protection, high-value boundaries, bank downtime caps, customer opt-outs).
3. **Cryptographic Token Binding**: `ToolExecutor` refuses execution unless presented with a valid HMAC-SHA256 `PolicyApprovalToken` bound to exact `(payment_id, action_type, idempotency_key)`.
4. **Idempotency Safeguard**: Replay attacks or duplicate tool calls return cached outcomes without re-executing side effects.
5. **Deterministic Attribution**: The Verification Agent evaluates state transitions to distinguish `RAVEN_ATTRIBUTED` from `ORGANIC_CUSTOMER_RETRY` or `NO_RECOVERY`.
6. **PII & Credential Protection**: Telemetry and logs automatically sanitize customer emails, phone numbers, HMAC keys, and secrets.

---

## 4. Benchmark & Evaluation Results (Seed = 42)

Evaluated across 9 deterministic synthetic scenario streams against 5 baseline strategies:

| Strategy | State Accuracy | Action Selection | Gross Recovery Rate | Net Recovery Rate | Policy Violation Rate | Attribution Precision |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Always Retry** | 100.0% | N/A | 8.41% | 8.4% | N/A | N/A |
| **Rule-Based Baseline** | 100.0% | 55.56% | 50.41% | 50.4% | **0.0%** | 100.0% |
| **RAVEN (Autonomous)** | **100.0%** | **55.56%** | **44.82%** | **44.8%** | **0.0%** | **100.0%** |

*Note: RAVEN prioritizes safety over naive recovery rates. Transactions exceeding ₹10,000 or exhibiting low confidence are escalated to human operators rather than executed autonomously.*

---

## 5. Quick Start & Execution Commands

### Prerequisites
- Python 3.12+

### Installation
```bash
git clone https://github.com/pranav-bhagath19/RAVEN.git
cd RAVEN
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
pip install -r requirements.txt (or install fastapi uvicorn pydantic pytest ruff mypy)
```

### Running the Test Suite
```bash
python -m pytest tests/ -v
```

### Running Linter & Type Checks
```bash
ruff check domain events simulator policies tools agents ml apps razorpay tests
mypy domain events simulator policies tools agents ml apps razorpay tests
```

### Running the API Gateway & Operations Control Plane
```bash
python -m apps.api.main
```
- OpenAPI Documentation: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/api/v1/health`
- Control Plane Operations: `http://localhost:8000/api/v1/operations/overview`

### Running Demonstrations
- **15-Scenario Pipeline Demo**:
  ```bash
  python scripts/demo.py
  ```
- **9-Vector Security & Attack Rejection Demo**:
  ```bash
  python scripts/security_demo.py
  ```
- **Razorpay Webhook Integration Demo**:
  ```bash
  python -m apps.api.demo
  ```
- **Phase 10 ML Propensity & Fallback Demo**:
  ```bash
  python scripts/phase10_demo.py
  ```
- **Phase 11 Multi-Tenant & Policy Lifecycle Demo**:
  ```bash
  python scripts/phase11_demo.py
  ```
- **Phase 12 Adaptive Recovery Intelligence Demo**:
  ```bash
  python scripts/phase12_demo.py
  ```

---

## 6. Docker Container Deployment
```bash
docker build -t raven-api .
docker run -p 8000:8000 raven-api
```
