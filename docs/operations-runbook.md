# RAVEN Production Operations & Incident Runbook

## 1. Production Service Startup & Readiness Probes

### HTTP API Health & Readiness Probes
- **Liveness Probe**: `GET /health/liveness` -> Returns HTTP `200 OK` `{"status": "UP"}`.
- **Readiness Probe**: `GET /health/readiness` -> Verifies database, Redis, and regional sync status. Returns `200 OK` when operational.

### Startup Command
```bash
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 2. Disaster Recovery & Failover Procedures

### PostgreSQL Outage / Degradation
1. **Symptom**: Database transaction timeouts or connection pool exhaustion.
2. **Action**:
   - Connection pool automatically uses `pool_pre_ping=True` to recycle broken connections.
   - Applications fail closed without emitting false success responses.
   - If primary database is unrecoverable, initiate read-replica promotion via standard DB failover.

### Redis Cache Disconnection
1. **Symptom**: Redis ping failures or socket timeouts.
2. **Action**:
   - `RedisIdempotencyStore` falls back to thread-safe in-memory idempotency check.
   - Zero duplicate tool execution occurs.
   - Once Redis reconnects, distributed caching resumes automatically.

### Regional Failover & Disaster Recovery
1. **Symptom**: Primary region (`ap-south-1`) becomes unresponsive or replication sync age exceeds 300 seconds.
2. **Action**:
   - `RegionalFailoverManager` flags region status as `DEGRADED` or `OFFLINE`.
   - Traffic routes automatically to secondary region (`us-east-1`).
   - If policy conflict is detected upon failover, `PolicyReconciler` evaluates lineage trees. If ambiguous, system fails closed.

---

## 3. Emergency Policy Rollback & Shutdown

### Emergency Policy Rollback
To rollback a merchant policy to a previous known-good version:
```bash
POST /api/v1/merchants/{merchant_id}/policies/rollback
Header: Authorization: Bearer <ADMIN_TOKEN>
Payload: {"target_version": 1}
```

### Emergency System Shutdown
To immediately halt tool execution:
1. Revoke `DEFAULT_POLICY_SECRET` environment variable or restart API instances with `RAVEN_EMERGENCY_SHUTDOWN=true`.
2. All `ToolExecutor` token verifications will immediately fail closed.
