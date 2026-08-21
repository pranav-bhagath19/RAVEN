# RAVEN Technical Demonstration Guide

## 1. Executive Summary

This document provides exact instructions for reviewing, testing, and evaluating the RAVEN system during technical demonstrations and jury presentations.

---

## 2. Available Demonstrations

### 1. Interactive 15-Scenario Pipeline Demo
Executes the full recovery lifecycle across 15 scenarios (transient timeouts, terminal captured blocks, high-value escalations, customer opt-outs, bank downtime caps, LLM fallbacks, and attribution verifications).
```bash
python scripts/demo.py
```

### 2. Zero-Trust Security Attack Rejection Demo
Simulates 9 attack vectors (policy bypass, forged signature, expired token, payment ID mismatch, action type mismatch, idempotency replay, and captured payment retry) and verifies that every attack is rejected safely.
```bash
python scripts/security_demo.py
```

### 3. Razorpay Webhook Ingestion Demo
Demonstrates raw Razorpay HTTP POST body handling, HMAC-SHA256 signature verification, canonical mapping, state reconstruction, and DecisionTrace correlation.
```bash
python -m apps.api.demo
```

### 4. Interactive OpenAPI / Swagger Documentation
Run the API gateway and inspect interactive endpoints in browser:
```bash
python -m apps.api.main
```
Open `http://localhost:8000/docs` in browser.
