# RAVEN Firebase System Architecture

## Overview
RAVEN (Revenue-aware Autonomous Verification & ENgine) has completely migrated its persistence and infrastructure layer from PostgreSQL and Redis to **Firebase Firestore** and **Firebase Authentication**.

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                            EXTERNAL CLIENTS                              │
│       Razorpay Webhooks (HTTPS)  │  Next.js Operations Dashboard        │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │ (HTTPS via Ngrok / REST API)
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                       RAVEN FASTAPI CONTROL PLANE                        │
│   - HMAC-SHA256 Webhook Ingestion & Deduplication                        │
│   - Multi-Tenant Isolation (tenant_id) & RBAC Authentication             │
│   - State Reconstruction & Financial Ledger                              │
│   - Autonomous Recovery Pipeline (RootCauseAnalyst, RecoveryPlanner)     │
│   - Propensity Model Scoring & Adaptive Bandit Intelligence              │
│   - PolicyEngine Veto Authority (POL_001 - POL_007)                      │
│   - HMAC-SHA256 PolicyApprovalToken Verification                         │
│   - ToolExecutor Execution Boundary & Verification Engine                │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │ (Firestore Admin SDK & Transactions)
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                       FIREBASE PERSISTENCE LAYER                         │
│   - Firebase Firestore Document Database (15 Document Collections)       │
│   - Firestore Atomic Transactional Idempotency & Distributed Lock Store  │
│   - Firebase Authentication & User API Key Hash Validation               │
└──────────────────────────────────────────────────────────────────────────┘
```

## Key Architectural Principles
1. **Zero Pipeline Regression**: Domain models, entity kernels, ML propensity models, PolicyEngine rules, ToolExecutor sandbox, and DecisionTrace lineage remain 100% frozen and untouched.
2. **1:1 Firestore Collection Mapping**: 15 persistent relational tables map directly to document collections in Firestore while maintaining integer paise currency calculations.
3. **Atomic Firestore Idempotency**: Redis is replaced by a Firestore document transaction lock adapter (`idempotency` collection), providing distributed key locking and regional scoping (`tenant_id:region_id:key`).
4. **Seamless Offline Emulation**: Includes a thread-safe in-memory Firestore emulator (`persistence/firebase.py`) so the entire 300-test suite runs offline without requiring live GCP credentials during local development or CI/CD.
