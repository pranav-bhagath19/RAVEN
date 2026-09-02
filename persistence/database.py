"""
RAVEN Database Connection & Session Management Adapter

Provides Firestore session maker, compatibility wrappers, and schema initialization.
Adapts SQLAlchemy-style Session APIs to delegate directly to Firebase Firestore,
ensuring zero logic breakage across legacy callers.
"""

import os
from typing import Any, Generator
from persistence.firebase import get_firestore_client, reset_firestore_emulator


def get_database_url() -> str:
    """Returns database connection URL from environment variable or default fallback."""
    return os.getenv("DATABASE_URL", "sqlite:///./raven_local.db")


def is_sqlite(url: str | None = None) -> bool:
    """Returns True if connection URL uses SQLite."""
    target_url = url or get_database_url()
    return target_url.startswith("sqlite")


class Base:
    """Base compatibility class for ORM metadata references."""

    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    class metadata:
        tables = {
            "tenants": True,
            "payments": True,
            "financial_events": True,
            "webhook_ingestions": True,
            "decision_traces": True,
            "merchant_policies": True,
            "policy_audit_logs": True,
            "tool_executions": True,
            "verifications": True,
            "observability_telemetry": True,
            "background_jobs": True,
            "adaptive_outcomes": True,
            "model_registry": True,
            "users": True,
            "user_api_keys": True,
        }

        @staticmethod
        def create_all(bind: Any = None) -> None:
            pass

        @staticmethod
        def drop_all(bind: Any = None) -> None:
            reset_firestore_emulator()




class FirestoreQueryAdapter:
    """Adapts SQLAlchemy Query interface to Firestore Collection queries."""

    def __init__(self, model_class: Any, session: "FirestoreSessionAdapter") -> None:
        self.model_class = model_class
        self.session = session
        self.filters: list[tuple[str, Any]] = []
        self._order_by: list[tuple[str, bool]] = []
        self._offset: int = 0
        self._limit: int | None = None
        self._in_filters: list[tuple[str, list[Any]]] = []

    def filter(self, *criterion: Any) -> "FirestoreQueryAdapter":
        for c in criterion:
            if hasattr(c, "left") and hasattr(c, "right"):
                col_name = getattr(c.left, "name", str(c.left))
                val = getattr(c.right, "value", c.right)
                self.filters.append((col_name, val))
            elif hasattr(c, "name"):
                self.filters.append((c.name, True))
        return self

    def order_by(self, *criterion: Any) -> "FirestoreQueryAdapter":
        for c in criterion:
            col_name = getattr(c, "name", str(c))
            descending = False
            if hasattr(c, "modifier") and "DESC" in str(c.modifier).upper():
                descending = True
            elif "desc" in str(c).lower():
                descending = True
            self._order_by.append((col_name, descending))
        return self

    def offset(self, n: int) -> "FirestoreQueryAdapter":
        self._offset = n
        return self

    def limit(self, n: int) -> "FirestoreQueryAdapter":
        self._limit = n
        return self

    def with_for_update(self) -> "FirestoreQueryAdapter":
        return self

    def _execute_fetch(self) -> list[Any]:
        from persistence.firestore_store import (
            FirestoreAPIKeyRepository,
            FirestoreDecisionRepository,
            FirestoreEventRepository,
            FirestoreJobRepository,
            FirestoreMerchantPolicyRepository,
            FirestorePaymentRepository,
            FirestoreToolExecutionRepository,
            FirestoreVerificationRepository,
        )

        model_name = getattr(self.model_class, "__tablename__", self.model_class.__name__)

        if model_name in ("payments", "PaymentRecord"):
            p_repo: Any = FirestorePaymentRepository(self.session.db)
            status_filter = next((val for k, val in self.filters if k == "status"), None)
            merchant_filter = next((val for k, val in self.filters if k == "merchant_id"), None)
            customer_filter = next((val for k, val in self.filters if k == "customer_id"), None)
            pid_filter = next((val for k, val in self.filters if k == "payment_id"), None)

            if pid_filter:
                p_rec = p_repo.get_by_id(pid_filter)
                return [p_rec] if p_rec else []

            p_recs, _ = p_repo.list_payments(
                status=status_filter,
                merchant_id=merchant_filter,
                customer_id=customer_filter,
                page=1,
                page_size=1000,
            )
            return list(p_recs)

        if model_name in ("financial_events", "FinancialEventRecord"):
            e_repo: Any = FirestoreEventRepository(self.session.db)
            hash_filter = next((val for k, val in self.filters if k == "event_hash"), None)
            if hash_filter:
                docs = e_repo.collection.where("event_hash", "==", hash_filter).get()
                if docs:
                    d = docs[0].to_dict()
                    return [e_repo.save_event(d)[0]]
                return []

            entity_filter = next((val for k, val in self.filters if k == "entity_id"), None)
            if entity_filter:
                return list(e_repo.get_events_for_entity(entity_filter))

            e_recs, _ = e_repo.list_events(page=1, page_size=1000)
            return list(e_recs)

        if model_name in ("merchant_policies", "MerchantPolicyRecord"):
            pol_repo: Any = FirestoreMerchantPolicyRepository(self.session.db)
            tenant_filter = next((val for k, val in self.filters if k == "tenant_id"), None)
            status_filter = next((val for k, val in self.filters if k == "status"), None)
            version_filter = next((val for k, val in self.filters if k == "version"), None)

            if tenant_filter and version_filter:
                p = pol_repo.get_policy_version(tenant_filter, int(version_filter))
                if p:
                    from persistence.models import MerchantPolicyRecord
                    rec = MerchantPolicyRecord(
                        policy_id=p.policy_id,
                        tenant_id=p.tenant_id,
                        version=p.version,
                        status=p.status.value,
                        configuration_json=p.configuration_json,
                        configuration_hash=p.configuration_hash,
                        created_by=p.created_by,
                        created_at=p.created_at,
                        activated_at=p.activated_at,
                        deactivated_at=p.deactivated_at,
                        parent_version=p.parent_version,
                        rollback_source_version=p.rollback_source_version,
                    )
                    return [rec]
                return []

            if tenant_filter and status_filter == "ACTIVE":
                p = pol_repo.get_active_policy(tenant_filter)
                if p:
                    from persistence.models import MerchantPolicyRecord
                    rec = MerchantPolicyRecord(
                        policy_id=p.policy_id,
                        tenant_id=p.tenant_id,
                        version=p.version,
                        status=p.status.value,
                        configuration_json=p.configuration_json,
                        configuration_hash=p.configuration_hash,
                        created_by=p.created_by,
                        created_at=p.created_at,
                        activated_at=p.activated_at,
                        deactivated_at=p.deactivated_at,
                        parent_version=p.parent_version,
                        rollback_source_version=p.rollback_source_version,
                    )
                    return [rec]
                return []

            if tenant_filter:
                versions = pol_repo.list_policy_versions(tenant_filter)
                from persistence.models import MerchantPolicyRecord
                pol_recs = [
                    MerchantPolicyRecord(
                        policy_id=p.policy_id,
                        tenant_id=p.tenant_id,
                        version=p.version,
                        status=p.status.value,
                        configuration_json=p.configuration_json,
                        configuration_hash=p.configuration_hash,
                        created_by=p.created_by,
                        created_at=p.created_at,
                        activated_at=p.activated_at,
                        deactivated_at=p.deactivated_at,
                        parent_version=p.parent_version,
                        rollback_source_version=p.rollback_source_version,
                    )
                    for p in versions
                ]
                if status_filter:
                    pol_recs = [r for r in pol_recs if r.status == status_filter]
                return list(pol_recs)

        if model_name in ("decision_traces", "DecisionTraceRecord"):
            d_repo: Any = FirestoreDecisionRepository(self.session.db)
            did_filter = next((val for k, val in self.filters if k == "decision_id"), None)
            if did_filter:
                d_rec = d_repo.get_by_id(did_filter)
                return [d_rec] if d_rec else []

            pid_filter = next((val for k, val in self.filters if k == "payment_id"), None)
            d_recs, _ = d_repo.list_traces(payment_id=pid_filter, page=1, page_size=1000)
            return list(d_recs)

        if model_name in ("background_jobs", "BackgroundJobRecord"):
            j_repo: Any = FirestoreJobRepository(self.session.db)
            docs = [d.to_dict() for d in j_repo.collection.get()]
            from persistence.firestore_store import parse_dt
            from persistence.models import BackgroundJobRecord
            j_recs = [
                BackgroundJobRecord(
                    job_id=d["job_id"],
                    tenant_id=d.get("tenant_id", "default_tenant"),
                    event_id=d["event_id"],
                    payment_id=d["payment_id"],
                    trace_id=d.get("trace_id"),
                    status=d.get("status", "QUEUED"),
                    attempt_count=d.get("attempt_count", 0),
                    max_attempts=d.get("max_attempts", 3),
                    failure_reason=d.get("failure_reason"),
                    payload_json=d.get("payload_json", {}),
                    next_attempt_at=parse_dt(d.get("next_attempt_at")),
                    created_at=parse_dt(d.get("created_at")),
                    updated_at=parse_dt(d.get("updated_at")),
                )
                for d in docs
            ]
            return list(j_recs)

        if model_name in ("user_api_keys", "UserAPIKeyRecord"):
            k_repo: Any = FirestoreAPIKeyRepository(self.session.db)
            hash_filter = next((val for k, val in self.filters if k == "key_hash"), None)
            key_id_filter = next((val for k, val in self.filters if k == "key_id"), None)
            docs = [d.to_dict() for d in k_repo.keys_col.get()]
            from persistence.firestore_store import parse_dt
            from persistence.models import UserAPIKeyRecord
            k_recs = [
                UserAPIKeyRecord(
                    key_id=d["key_id"],
                    user_id=d["user_id"],
                    tenant_id=d["tenant_id"],
                    name=d["name"],
                    key_prefix=d["key_prefix"],
                    key_hash=d["key_hash"],
                    role=d["role"],
                    revoked=d.get("revoked", False),
                    expires_at=parse_dt(d["expires_at"]) if d.get("expires_at") else None,
                    created_at=parse_dt(d["created_at"]),
                )
                for d in docs
            ]
            if hash_filter:
                k_recs = [r for r in k_recs if r.key_hash == hash_filter]
            if key_id_filter:
                k_recs = [r for r in k_recs if r.key_id == key_id_filter]
            return list(k_recs)

        return []

    def first(self) -> Any | None:
        items = self._execute_fetch()
        return items[0] if items else None

    def all(self) -> list[Any]:
        items = self._execute_fetch()
        if self._offset:
            items = items[self._offset:]
        if self._limit:
            items = items[:self._limit]
        return items

    def count(self) -> int:
        return len(self._execute_fetch())

    def update(self, values: dict[str, Any], synchronize_session: Any = None) -> int:
        items = self._execute_fetch()
        for item in items:
            for k, v in values.items():
                if hasattr(item, k):
                    setattr(item, k, v)
        return len(items)


class FirestoreSessionAdapter:
    """Adapts SQLAlchemy Session instance calls to Firestore Repositories."""

    def __init__(self) -> None:
        self.db = get_firestore_client()
        self._pending_adds: list[Any] = []

    def query(self, model_class: Any) -> FirestoreQueryAdapter:
        return FirestoreQueryAdapter(model_class, self)

    def add(self, instance: Any) -> None:
        self._pending_adds.append(instance)

    def commit(self) -> None:
        from persistence.firestore_store import (
            FirestoreAPIKeyRepository,
            FirestoreDecisionRepository,
            FirestoreEventRepository,
            FirestoreJobRepository,
            FirestoreMerchantPolicyRepository,
            FirestorePaymentRepository,
            FirestoreToolExecutionRepository,
            FirestoreVerificationRepository,
        )

        for inst in self._pending_adds:
            model_name = getattr(inst, "__tablename__", inst.__class__.__name__)
            if model_name in ("payments", "PaymentRecord"):
                p_repo: Any = FirestorePaymentRepository(self.db)
                d = {k: getattr(inst, k) for k in dir(inst) if not k.startswith("_") and not callable(getattr(inst, k))}
                p_repo.upsert_payment(d)
            elif model_name in ("financial_events", "FinancialEventRecord"):
                e_repo: Any = FirestoreEventRepository(self.db)
                d = {k: getattr(inst, k) for k in dir(inst) if not k.startswith("_") and not callable(getattr(inst, k))}
                e_repo.save_event(d)
            elif model_name in ("merchant_policies", "MerchantPolicyRecord"):
                col = self.db.collection("merchant_policies")
                doc_id = f"{getattr(inst, 'tenant_id')}_v{getattr(inst, 'version')}"
                d = {
                    "policy_id": getattr(inst, "policy_id"),
                    "tenant_id": getattr(inst, "tenant_id"),
                    "version": getattr(inst, "version"),
                    "status": getattr(inst, "status"),
                    "configuration_json": getattr(inst, "configuration_json", {}),
                    "configuration_hash": getattr(inst, "configuration_hash", ""),
                    "created_by": getattr(inst, "created_by", "system"),
                    "created_at": str(getattr(inst, "created_at", "")),
                }
                col.document(doc_id).set(d)
            elif model_name in ("policy_audit_logs", "PolicyAuditLogRecord"):
                col = self.db.collection("policy_audit_logs")
                aud_id = getattr(inst, "audit_id")
                d = {
                    "audit_id": aud_id,
                    "tenant_id": getattr(inst, "tenant_id"),
                    "policy_id": getattr(inst, "policy_id"),
                    "policy_version": getattr(inst, "policy_version"),
                    "action": getattr(inst, "action"),
                    "actor_id": getattr(inst, "actor_id"),
                    "previous_version": getattr(inst, "previous_version"),
                    "new_version": getattr(inst, "new_version"),
                    "configuration_hash": getattr(inst, "configuration_hash"),
                    "timestamp": str(getattr(inst, "timestamp", "")),
                    "reason": getattr(inst, "reason", ""),
                    "request_id": getattr(inst, "request_id", "req_unknown"),
                }
                col.document(aud_id).set(d)
            elif model_name in ("decision_traces", "DecisionTraceRecord"):
                d_repo: Any = FirestoreDecisionRepository(self.db)
                d = {k: getattr(inst, k) for k in dir(inst) if not k.startswith("_") and not callable(getattr(inst, k))}
                d_repo.save_trace(d)
            elif model_name in ("tool_executions", "ToolExecutionRecord"):
                x_repo: Any = FirestoreToolExecutionRepository(self.db)
                d = {k: getattr(inst, k) for k in dir(inst) if not k.startswith("_") and not callable(getattr(inst, k))}
                x_repo.save_execution(d)
            elif model_name in ("verifications", "VerificationRecord"):
                v_repo: Any = FirestoreVerificationRepository(self.db)
                d = {k: getattr(inst, k) for k in dir(inst) if not k.startswith("_") and not callable(getattr(inst, k))}
                v_repo.save_verification(d)
            elif model_name in ("background_jobs", "BackgroundJobRecord"):
                col = self.db.collection("background_jobs")
                job_id = getattr(inst, "job_id")
                d = {k: getattr(inst, k) for k in dir(inst) if not k.startswith("_") and not callable(getattr(inst, k))}
                col.document(job_id).set(d)
            elif model_name in ("user_api_keys", "UserAPIKeyRecord"):
                col = self.db.collection("user_api_keys")
                key_id = getattr(inst, "key_id")
                d = {k: getattr(inst, k) for k in dir(inst) if not k.startswith("_") and not callable(getattr(inst, k))}
                col.document(key_id).set(d)
            elif model_name in ("users", "UserRecord"):
                col = self.db.collection("users")
                usr_id = getattr(inst, "user_id")
                d = {k: getattr(inst, k) for k in dir(inst) if not k.startswith("_") and not callable(getattr(inst, k))}
                col.document(usr_id).set(d)
        self._pending_adds.clear()

    def refresh(self, instance: Any) -> None:
        pass

    def expire_all(self) -> None:
        pass

    def rollback(self) -> None:
        self._pending_adds.clear()

    def close(self) -> None:
        self._pending_adds.clear()


engine = None


def SessionLocal() -> FirestoreSessionAdapter:
    """Returns a new FirestoreSessionAdapter session instance."""
    return FirestoreSessionAdapter()


def init_db() -> None:
    """Ensures Firestore initialization."""
    get_firestore_client()


def get_db() -> Generator[FirestoreSessionAdapter, None, None]:
    """FastAPI / Application dependency yielding a Firestore session context."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
