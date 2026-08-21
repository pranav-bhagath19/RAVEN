# RAVEN Production Deployment & Environment Guide

## 1. Overview

RAVEN is designed to run as a stateless, lightweight FastAPI HTTP Gateway and control plane service.

## 2. Environment Variables

Set the following variables in production or staging environments:

| Variable Name | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `RAVEN_ENV` | Optional | `demo` | Environment mode: `development`, `demo`, `production` |
| `API_HOST` | Optional | `0.0.0.0` | Server host binding address |
| `API_PORT` | Optional | `8000` | Server port binding |
| `DEBUG` | Optional | `false` | Enable verbose debug responses (Keep `false` in production) |
| `RAZORPAY_KEY_ID` | Required | `rzp_test_...` | Razorpay Merchant API Key ID |
| `RAZORPAY_KEY_SECRET` | Required | `placeholder` | Razorpay Merchant API Key Secret |
| `RAZORPAY_WEBHOOK_SECRET` | Required | `placeholder` | Razorpay Webhook HMAC Signature Verification Secret |
| `RAVEN_POLICY_SECRET` | Required | `secret_2026` | Secret key used for signing HMAC `PolicyApprovalToken` tokens |
| `CORS_ORIGINS` | Optional | `*` | Comma-separated CORS allowed origins list |

---

## 3. Local & Server Deployment Steps

### Standalone Server Run (Uvicorn)
```bash
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Container Deployment
```bash
docker build -t raven-api:v1.0 .
docker run -d --name raven -p 8000:8000 --env-file .env raven-api:v1.0
```

---

## 4. Operational Probes & Health Checks
- **Liveness Probe**: `GET /health` or `GET /api/v1/health` (Returns `{"status": "ok", "service": "raven"}`)
- **Readiness Probe**: `GET /api/v1/operations/ready` (Returns `{"status": "ready"}`)
- **Control Plane Status**: `GET /api/v1/operations/health` (Returns full subsystem status breakdown)
