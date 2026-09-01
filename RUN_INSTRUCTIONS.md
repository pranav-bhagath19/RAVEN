# RAVEN — Project Run & Terminal Instructions Guide

This guide provides step-by-step terminal commands to set up, run, test, and containerize all components of **RAVEN** (Frontend Dashboard, Backend API, Worker Process, Demos, and Docker Stack).

---

## 📋 Table of Contents
1. [Prerequisites & Initial Setup](#1-prerequisites--initial-setup)
2. [Running Components Locally (Manual Step-by-Step)](#2-running-components-locally-manual-step-by-step)
   - [Backend API Gateway](#a-backend-api-gateway)
   - [Frontend Operations Dashboard](#b-frontend-operations-dashboard)
   - [Background Recovery Worker](#c-background-recovery-worker)
3. [Running via Docker Compose (All-in-One)](#3-running-via-docker-compose-all-in-one)
4. [Running Demos & Benchmarks](#4-running-demos--benchmarks)
5. [Running Test Suite & Code Quality Checks](#5-running-test-suite--code-quality-checks)
6. [Webhook Tunneling (Ngrok Setup)](#6-webhook-tunneling-ngrok-setup)
7. [Quick Terminal Commands Summary](#7-quick-terminal-commands-summary)

---

## 1. Prerequisites & Initial Setup

### Requirements
- **Python**: 3.12 or higher
- **Node.js**: v18+ & **npm**: v9+ (for Frontend Dashboard)
- **Docker & Docker Compose** (Optional, for containerized run)

### Step 1: Clone Repository & Create Environment File
Open your terminal in the project root (`c:\Users\prana\Documents\RAVEN` or equivalent):

```bash
# Copy example environment configuration file to .env
# Windows (PowerShell / CMD):
copy .env.example .env

# Linux / macOS:
cp .env.example .env
```

### Step 2: Set Up Python Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate Virtual Environment:
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1

# On Windows Command Prompt (CMD):
.\venv\Scripts\activate.bat

# On Linux / macOS:
source venv/bin/activate

# Install Python dependencies
pip install fastapi uvicorn pydantic pydantic-settings httpx pytest ruff mypy
```

### Step 3: Install Frontend Dependencies
```bash
# Navigate to dashboard directory and install node modules
cd apps/dashboard
npm install
cd ../..
```

---

## 2. Running Components Locally (Manual Step-by-Step)

To run the full stack locally without Docker, open **3 separate terminal windows** (ensure virtual environment is activated in each).

### A. Backend API Gateway
The API Gateway handles webhooks, state reconstruction, policy approvals, and operation control plane endpoints.

**Terminal 1 (Project Root):**
```bash
# Option 1: Direct Python module execution
python -m apps.api.main

# Option 2: Uvicorn with auto-reload (Development mode)
uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```
- **API URL**: `http://localhost:8000`
- **Interactive OpenAPI (Swagger) Docs**: `http://localhost:8000/docs`
- **Health Check Endpoint**: `http://localhost:8000/api/v1/health`

---

### B. Frontend Operations Dashboard
The Next.js interactive dashboard provides the Operations Control Plane UI.

**Terminal 2 (`apps/dashboard` directory):**
```bash
# Navigate to dashboard directory
cd apps/dashboard

# Run Next.js development server
npm run dev
```
- **Dashboard URL**: `http://localhost:3000`

---

### C. Background Recovery Worker
The worker polls the queue for pending payment recovery tasks and executes authorized actions.

**Terminal 3 (Project Root):**
```bash
python -c "from apps.worker.worker import RecoveryWorker; RecoveryWorker().run_loop()"
```

---

## 3. Running via Docker Compose (All-in-One)

Docker Compose starts PostgreSQL, Redis, API Gateway, Background Worker, and Frontend Dashboard simultaneously in isolated containers.

```bash
# Build and start all services in foreground
docker-compose up --build

# Or start in detached (background) mode
docker-compose up -d --build

# View logs for all running containers
docker-compose logs -f

# View logs for a specific service (e.g., api or dashboard)
docker-compose logs -f raven-api
docker-compose logs -f dashboard

# Stop and remove all running containers
docker-compose down
```

### Container Endpoints:
- **Frontend Dashboard**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`

---

## 4. Running Demos & Benchmarks

RAVEN includes 8 built-in interactive demonstration scripts, stress tests, and certification harnesses to test autonomous recovery pipelines under realistic scenarios.

Ensure your virtual environment is active in the project root:

### 1. 15-Scenario Pipeline & Recovery Demo
Executes 15 synthetic failure scenarios (network timeout, card limit, bank downtime, PII sanitization, etc.) through the core RAVEN state machine.
```bash
python scripts/demo.py
```

### 2. 9-Vector Security & Attack Rejection Demo
Tests defense mechanisms against signature spoofing, invalid policy approval tokens, unauthorized side effects, and PII leakage.
```bash
python scripts/security_demo.py
```

### 3. Razorpay Webhook Integration & Test Mode Demo
Simulates Razorpay webhook payloads (`payment.failed`) and validates state reconstruction against live/mock API endpoints.
```bash
python -m apps.api.demo
```

### 4. Phase 10 ML Propensity & Fallback Strategy Demo
Demonstrates ML propensity modeling combined with heuristic fallbacks for calculating expected transaction recovery value.
```bash
python scripts/phase10_demo.py
```

### 5. Phase 11 Multi-Tenant & Policy Lifecycle Demo
Demonstrates policy rule evaluation across isolated merchant tenant contexts.
```bash
python scripts/phase11_demo.py
```

### 6. Phase 14 Multi-Region Reliability & Replication Demo
Tests database failover, ledger replication, and non-timestamp sequence tie-breaking across multi-region nodes.
```bash
python scripts/phase14_demo.py
```

### 7. Phase 15 Production Certification Harness
Runs end-to-end verification of all safety invariants, policy compliance, and token-binding security before deployment.
```bash
python scripts/phase15_certification.py
```

### 8. Phase 15 Performance Benchmark Harness
Measures throughput, latency, and state reconstruction performance under synthetic load (Seed = 42).
```bash
python scripts/phase15_benchmark.py
```

---

## 5. Running Test Suite & Code Quality Checks

### Run Unit & Integration Tests (Pytest)
```bash
# Run all tests in the repository with verbose output
python -m pytest tests/ -v

# Run specific test suites
python -m pytest tests/test_security.py -v
python -m pytest tests/test_state_machine.py -v
python -m pytest tests/test_policy_engine.py -v
```

### Run Code Quality, Formatting & Static Type Checks
```bash
# 1. Run Ruff Linter across all Python packages
ruff check domain events simulator policies tools agents ml apps razorpay tests

# 2. Run Mypy Static Type Checker
mypy domain events simulator policies tools agents ml apps razorpay tests

# 3. Run Frontend Linter (Next.js & ESLint)
cd apps/dashboard
npm run lint
cd ../..
```

---

## 6. Webhook Tunneling (Ngrok Setup)

### Why Ngrok is Required
During local development, Razorpay's servers cannot reach `http://localhost:8000` directly over the internet. **Ngrok** creates a secure public HTTPS URL (e.g. `https://xxxx.ngrok-free.app`) forwarding incoming webhooks directly to your local FastAPI server.

### Prerequisites
Install the official `ngrok` Python SDK in your virtual environment:
```bash
pip install ngrok
```

### Step-by-Step Ngrok Configuration & Run

#### Step 1: Configure Credentials in `.env`
Open your `.env` file and set your Ngrok authentication token and static domain (free from [ngrok dashboard](https://dashboard.ngrok.com/domains)):
```env
NGROK_AUTHTOKEN=your_ngrok_authtoken_here
NGROK_DOMAIN=your-static-domain.ngrok-free.app
```

#### Step 2: Start the Tunnel Forwarder
Run the Python tunnel forwarder script:
```bash
python scripts/start_ngrok_tunnel.py
```

*Output Example:*
```
========================================================================
  RAVEN — NGROK WEBHOOK TUNNEL FORWARDER
========================================================================

  [STEP 1/2] Connecting ngrok tunnel to localhost:8000...
  [STEP 2/2] Public Tunnel Established!
  -> Base Public URL:  https://xxxx-xx-xx.ngrok-free.app
  -> Razorpay Webhook: https://xxxx-xx-xx.ngrok-free.app/api/v1/webhooks/razorpay
```

#### Step 3: Register Webhook in Razorpay Dashboard
1. Log in to [Razorpay Dashboard](https://dashboard.razorpay.com/) (Ensure **Test Mode** toggle is ON).
2. Go to **Settings** ➔ **Webhooks** ➔ **Add New Webhook**.
3. Set **Webhook URL** to: `https://<your-ngrok-domain>/api/v1/webhooks/razorpay`
4. Set **Secret** to match `RAZORPAY_WEBHOOK_SECRET` in your `.env`.
5. Select event: `payment.failed`.
6. Save the webhook. Live payment failure events will now trigger your local RAVEN engine!

---

## 7. Quick Terminal Commands Summary

| Component / Task | Command | Directory | Output / Target |
| :--- | :--- | :--- | :--- |
| **Backend API** | `python -m apps.api.main` | Project Root | `http://localhost:8000` |
| **Frontend UI** | `npm run dev` | `apps/dashboard` | `http://localhost:3000` |
| **Worker Process** | `python -c "from apps.worker.worker import RecoveryWorker; RecoveryWorker().run_loop()"` | Project Root | Background Loop |
| **Docker Full Stack** | `docker-compose up --build` | Project Root | Containers for API, UI, Worker, Postgres, Redis |
| **Ngrok Tunnel** | `python scripts/start_ngrok_tunnel.py` | Project Root | Exposes `:8000` for Razorpay Webhooks |
| **Main Pipeline Demo** | `python scripts/demo.py` | Project Root | 15 Failure Scenarios |
| **Security Demo** | `python scripts/security_demo.py` | Project Root | 9 Attack Vectors Rejection |
| **Pytest Suite** | `python -m pytest tests/ -v` | Project Root | Complete Test Pass |
| **Python Linter** | `ruff check .` | Project Root | Code Formatting Checks |

