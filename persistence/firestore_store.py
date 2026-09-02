"""
RAVEN Firestore Production Repositories & Data Layer

Provides 100% signature-compatible Firestore persistent repositories for Tenants, Payments,
Financial Events, Decision Traces, Merchant Policies, Policy Audit Logs, Tool Executions,
Verifications, Webhooks, Telemetry, Background Jobs, Adaptive Outcomes, Model Registry,
Users, and API Keys.
"""

from datetime import datetime, timezone
import hashlib
import secrets
import threading
import time
from typing import Any, cast
from domain.entities.merchant_policy import (
    MerchantPolicyVersion,
    PolicyAuditAction,
    PolicyAuditLog,
    PolicyVersionStatus,
)
from persistence.firebase import get_firestore_client
from persistence.models import (
    BackgroundJobRecord,
    DecisionTraceRecord,
    FinancialEventRecord,
    PaymentRecord,
    ToolExecutionRecord,
    UserAPIKeyRecord,
    UserRecord,
    VerificationRecord,
    WebhookRecord,
)
from policies.validation import compute_policy_config_hash


def parse_dt(val: Any) -> datetime:
    """Helper to convert ISO strings, timestamps, or datetimes to timezone-aware UTC datetime."""
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(val, tz=timezone.utc)
    if isinstance(val, str):
        try:
            dt = datetime.fromisoformat(val)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return datetime.now(timezone.utc)


def format_dt(dt: datetime | None) -> str | None:
    """Helper to convert datetime to ISO 8601 string format."""
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    return dt.isoformat()


class FirestorePaymentRepository:
    """Firestore Repository for Payment entities."""

    def __init__(self, db: Any = None) -> None:
        self.db = db or get_firestore_client()
        self.collection = self.db.collection("payments")

    def upsert_payment(self, payment_data: dict[str, Any]) -> PaymentRecord:
        data = dict(payment_data)
        pid = data["payment_id"]
        now = datetime.now(timezone.utc)
        data["updated_at"] = format_dt(now)
        if "created_at" in data:
            data["created_at"] = format_dt(parse_dt(data["created_at"]))
        else:
            data["created_at"] = format_dt(now)

        doc_ref = self.collection.document(pid)
        doc = doc_ref.get()

        if doc.exists:
            existing = doc.to_dict()
            existing.update(data)
            doc_ref.set(existing)
            merged = existing
        else:
            doc_ref.set(data)
            merged = data

        return PaymentRecord(
            payment_id=merged.get("payment_id", pid),
            tenant_id=merged.get("tenant_id", "default_tenant"),
            order_id=merged.get("order_id"),
            merchant_id=merged.get("merchant_id", "mer_default"),
            customer_id=merged.get("customer_id", "cust_default"),
            amount_minor=merged.get("amount_minor", 0),
            currency=merged.get("currency", "INR"),
            status=merged.get("status", "failed"),
            attempts_count=merged.get("attempts_count", 0),
            error_code=merged.get("error_code"),
            error_description=merged.get("error_description"),
            created_at=parse_dt(merged.get("created_at")),
            updated_at=parse_dt(merged.get("updated_at")),
        )

    def get_by_id(self, payment_id: str) -> PaymentRecord | None:
        doc = self.collection.document(payment_id).get()
        if not doc.exists:
            return None
        d = doc.to_dict()
        return PaymentRecord(
            payment_id=d.get("payment_id", payment_id),
            tenant_id=d.get("tenant_id", "default_tenant"),
            order_id=d.get("order_id"),
            merchant_id=d.get("merchant_id", "mer_default"),
            customer_id=d.get("customer_id", "cust_default"),
            amount_minor=d.get("amount_minor", 0),
            currency=d.get("currency", "INR"),
            status=d.get("status", "failed"),
            attempts_count=d.get("attempts_count", 0),
            error_code=d.get("error_code"),
            error_description=d.get("error_description"),
            created_at=parse_dt(d.get("created_at")),
            updated_at=parse_dt(d.get("updated_at")),
        )

    def list_payments(
        self,
        status: str | None = None,
        merchant_id: str | None = None,
        customer_id: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[PaymentRecord], int]:
        docs = [d.to_dict() for d in self.collection.get()]
        filtered: list[dict[str, Any]] = []

        for d in docs:
            if status and d.get("status") != status:
                continue
            if merchant_id and d.get("merchant_id") != merchant_id:
                continue
            if customer_id and d.get("customer_id") != customer_id:
                continue
            filtered.append(d)

        filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = filtered[start:end]

        records = [
            PaymentRecord(
                payment_id=d.get("payment_id"),
                tenant_id=d.get("tenant_id", "default_tenant"),
                order_id=d.get("order_id"),
                merchant_id=d.get("merchant_id"),
                customer_id=d.get("customer_id"),
                amount_minor=d.get("amount_minor", 0),
                currency=d.get("currency", "INR"),
                status=d.get("status", "failed"),
                attempts_count=d.get("attempts_count", 0),
                error_code=d.get("error_code"),
                error_description=d.get("error_description"),
                created_at=parse_dt(d.get("created_at")),
                updated_at=parse_dt(d.get("updated_at")),
            )
            for d in page_items
        ]
        return records, total


class FirestoreEventRepository:
    """Firestore Repository for Financial Events log."""

    _save_lock = threading.Lock()
    _seen_hashes: set[str] = set()

    def __init__(self, db: Any = None) -> None:
        self.db = db or get_firestore_client()
        self.collection = self.db.collection("financial_events")

    def save_event(self, event_data: dict[str, Any]) -> tuple[FinancialEventRecord, bool]:
        with self._save_lock:
            data = dict(event_data)
            event_hash = data["event_hash"]
            event_id = data.get("event_id") or f"evt_{int(time.time() * 1000)}"
            data["event_id"] = event_id

            if isinstance(data.get("occurred_at"), datetime):
                data["occurred_at"] = format_dt(data["occurred_at"])
            elif not data.get("occurred_at"):
                data["occurred_at"] = format_dt(datetime.now(timezone.utc))

            if isinstance(data.get("received_at"), datetime):
                data["received_at"] = format_dt(data["received_at"])
            else:
                data["received_at"] = format_dt(datetime.now(timezone.utc))

            if event_hash in self._seen_hashes:
                rec = FinancialEventRecord(
                    event_id=event_id,
                    tenant_id=data.get("tenant_id", "default_tenant"),
                    event_hash=event_hash,
                    event_type=data["event_type"],
                    entity_id=data["entity_id"],
                    merchant_id=data.get("merchant_id", "mer_default"),
                    amount_minor=data.get("amount_minor"),
                    currency=data.get("currency", "INR"),
                    sequence_number=data.get("sequence_number", 0),
                    occurred_at=parse_dt(data["occurred_at"]),
                    received_at=parse_dt(data["received_at"]),
                    payload_json=data.get("payload_json", {}),
                )
                return rec, False

            doc_ref = self.collection.document(event_id)
            doc = doc_ref.get()
            if doc.exists:
                d = doc.to_dict()
                rec = FinancialEventRecord(
                    event_id=d["event_id"],
                    tenant_id=d.get("tenant_id", "default_tenant"),
                    event_hash=d["event_hash"],
                    event_type=d["event_type"],
                    entity_id=d["entity_id"],
                    merchant_id=d.get("merchant_id", "mer_default"),
                    amount_minor=d.get("amount_minor"),
                    currency=d.get("currency", "INR"),
                    sequence_number=d.get("sequence_number", 0),
                    occurred_at=parse_dt(d["occurred_at"]),
                    received_at=parse_dt(d["received_at"]),
                    payload_json=d.get("payload_json", {}),
                )
                self._seen_hashes.add(event_hash)
                return rec, False

            existing_docs = self.collection.where("event_hash", "==", event_hash).get()
            if existing_docs:
                d = existing_docs[0].to_dict()
                rec = FinancialEventRecord(
                    event_id=d["event_id"],
                    tenant_id=d.get("tenant_id", "default_tenant"),
                    event_hash=d["event_hash"],
                    event_type=d["event_type"],
                    entity_id=d["entity_id"],
                    merchant_id=d.get("merchant_id", "mer_default"),
                    amount_minor=d.get("amount_minor"),
                    currency=d.get("currency", "INR"),
                    sequence_number=d.get("sequence_number", 0),
                    occurred_at=parse_dt(d["occurred_at"]),
                    received_at=parse_dt(d["received_at"]),
                    payload_json=d.get("payload_json", {}),
                )
                self._seen_hashes.add(event_hash)
                return rec, False

            doc_ref.set(data)
            self._seen_hashes.add(event_hash)

            rec = FinancialEventRecord(
                event_id=event_id,
                tenant_id=data.get("tenant_id", "default_tenant"),
                event_hash=event_hash,
                event_type=data["event_type"],
                entity_id=data["entity_id"],
                merchant_id=data.get("merchant_id", "mer_default"),
                amount_minor=data.get("amount_minor"),
                currency=data.get("currency", "INR"),
                sequence_number=data.get("sequence_number", 0),
                occurred_at=parse_dt(data["occurred_at"]),
                received_at=parse_dt(data["received_at"]),
                payload_json=data.get("payload_json", {}),
            )
            return rec, True

    def get_events_for_entity(self, entity_id: str) -> list[FinancialEventRecord]:
        docs = self.collection.where("entity_id", "==", entity_id).get()
        data_list = [d.to_dict() for d in docs]
        data_list.sort(key=lambda x: (x.get("occurred_at", ""), x.get("sequence_number", 0)))
        return [
            FinancialEventRecord(
                event_id=d["event_id"],
                tenant_id=d.get("tenant_id", "default_tenant"),
                event_hash=d["event_hash"],
                event_type=d["event_type"],
                entity_id=d["entity_id"],
                merchant_id=d.get("merchant_id", "mer_default"),
                amount_minor=d.get("amount_minor"),
                currency=d.get("currency", "INR"),
                sequence_number=d.get("sequence_number", 0),
                occurred_at=parse_dt(d["occurred_at"]),
                received_at=parse_dt(d["received_at"]),
                payload_json=d.get("payload_json", {}),
            )
            for d in data_list
        ]

    def list_events(
        self,
        entity_id: str | None = None,
        event_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[FinancialEventRecord], int]:
        docs = [d.to_dict() for d in self.collection.get()]
        filtered: list[dict[str, Any]] = []

        for d in docs:
            if entity_id and d.get("entity_id") != entity_id:
                continue
            if event_type and d.get("event_type") != event_type:
                continue
            filtered.append(d)

        filtered.sort(key=lambda x: x.get("received_at", ""), reverse=True)
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = filtered[start:end]

        records = [
            FinancialEventRecord(
                event_id=d["event_id"],
                tenant_id=d.get("tenant_id", "default_tenant"),
                event_hash=d["event_hash"],
                event_type=d["event_type"],
                entity_id=d["entity_id"],
                merchant_id=d.get("merchant_id", "mer_default"),
                amount_minor=d.get("amount_minor"),
                currency=d.get("currency", "INR"),
                sequence_number=d.get("sequence_number", 0),
                occurred_at=parse_dt(d["occurred_at"]),
                received_at=parse_dt(d["received_at"]),
                payload_json=d.get("payload_json", {}),
            )
            for d in page_items
        ]
        return records, total


class FirestoreMerchantPolicyRepository:
    """Firestore Repository managing tenant merchant policy versions and audit logs."""

    def __init__(self, db: Any = None) -> None:
        self.db = db or get_firestore_client()
        self.policies_col = self.db.collection("merchant_policies")
        self.audit_col = self.db.collection("policy_audit_logs")

    def get_latest_version_number(self, tenant_id: str) -> int:
        docs = self.policies_col.where("tenant_id", "==", tenant_id).get()
        if not docs:
            return 0
        versions = [int(d.to_dict().get("version", 0)) for d in docs]
        return max(versions) if versions else 0

    def get_active_policy(self, tenant_id: str) -> MerchantPolicyVersion | None:
        docs = self.policies_col.where("tenant_id", "==", tenant_id).where("status", "==", PolicyVersionStatus.ACTIVE.value).get()
        if not docs:
            return None
        d = docs[0].to_dict()
        return MerchantPolicyVersion(
            policy_id=str(d["policy_id"]),
            tenant_id=str(d["tenant_id"]),
            version=int(d["version"]),
            status=PolicyVersionStatus(str(d["status"])),
            configuration_json=cast(dict[str, Any], d.get("configuration_json", {})),
            configuration_hash=str(d["configuration_hash"]),
            created_by=str(d.get("created_by", "system")),
            created_at=parse_dt(d["created_at"]),
            activated_at=parse_dt(d["activated_at"]) if d.get("activated_at") else None,
            deactivated_at=parse_dt(d["deactivated_at"]) if d.get("deactivated_at") else None,
            parent_version=int(d["parent_version"]) if d.get("parent_version") else None,
            rollback_source_version=int(d["rollback_source_version"]) if d.get("rollback_source_version") else None,
        )

    def get_policy_version(self, tenant_id: str, version: int) -> MerchantPolicyVersion | None:
        doc_id = f"{tenant_id}_v{version}"
        doc = self.policies_col.document(doc_id).get()
        if not doc.exists:
            docs = self.policies_col.where("tenant_id", "==", tenant_id).where("version", "==", version).get()
            if not docs:
                return None
            d = docs[0].to_dict()
        else:
            d = doc.to_dict()

        return MerchantPolicyVersion(
            policy_id=str(d["policy_id"]),
            tenant_id=str(d["tenant_id"]),
            version=int(d["version"]),
            status=PolicyVersionStatus(str(d["status"])),
            configuration_json=cast(dict[str, Any], d.get("configuration_json", {})),
            configuration_hash=str(d["configuration_hash"]),
            created_by=str(d.get("created_by", "system")),
            created_at=parse_dt(d["created_at"]),
            activated_at=parse_dt(d["activated_at"]) if d.get("activated_at") else None,
            deactivated_at=parse_dt(d["deactivated_at"]) if d.get("deactivated_at") else None,
            parent_version=int(d["parent_version"]) if d.get("parent_version") else None,
            rollback_source_version=int(d["rollback_source_version"]) if d.get("rollback_source_version") else None,
        )

    def list_policy_versions(self, tenant_id: str) -> list[MerchantPolicyVersion]:
        docs = self.policies_col.where("tenant_id", "==", tenant_id).get()
        data_list = [d.to_dict() for d in docs]
        data_list.sort(key=lambda x: int(x.get("version", 0)), reverse=True)
        return [
            MerchantPolicyVersion(
                policy_id=str(d["policy_id"]),
                tenant_id=str(d["tenant_id"]),
                version=int(d["version"]),
                status=PolicyVersionStatus(str(d["status"])),
                configuration_json=cast(dict[str, Any], d.get("configuration_json", {})),
                configuration_hash=str(d["configuration_hash"]),
                created_by=str(d.get("created_by", "system")),
                created_at=parse_dt(d["created_at"]),
                activated_at=parse_dt(d["activated_at"]) if d.get("activated_at") else None,
                deactivated_at=parse_dt(d["deactivated_at"]) if d.get("deactivated_at") else None,
                parent_version=int(d["parent_version"]) if d.get("parent_version") else None,
                rollback_source_version=int(d["rollback_source_version"]) if d.get("rollback_source_version") else None,
            )
            for d in data_list
        ]

    def create_draft_version(
        self,
        tenant_id: str,
        policy_id: str,
        configuration_json: dict[str, Any],
        actor_id: str = "system",
        request_id: str = "req_unknown",
    ) -> MerchantPolicyVersion:
        latest = self.get_latest_version_number(tenant_id)
        new_version_num = latest + 1
        cfg_hash = compute_policy_config_hash(configuration_json)
        now = datetime.now(timezone.utc)

        doc_id = f"{tenant_id}_v{new_version_num}"
        rec_data = {
            "policy_id": policy_id,
            "tenant_id": tenant_id,
            "version": new_version_num,
            "status": PolicyVersionStatus.DRAFT.value,
            "configuration_json": configuration_json,
            "configuration_hash": cfg_hash,
            "created_by": actor_id,
            "created_at": format_dt(now),
            "parent_version": latest if latest > 0 else None,
        }
        self.policies_col.document(doc_id).set(rec_data)

        audit_id = f"aud_{new_version_num}_{now.timestamp()}"
        audit_data = {
            "audit_id": audit_id,
            "tenant_id": tenant_id,
            "policy_id": policy_id,
            "policy_version": new_version_num,
            "action": PolicyAuditAction.CREATED.value,
            "actor_id": actor_id,
            "previous_version": latest if latest > 0 else None,
            "new_version": new_version_num,
            "configuration_hash": cfg_hash,
            "timestamp": format_dt(now),
            "reason": f"Created draft policy version {new_version_num}",
            "request_id": request_id,
        }
        self.audit_col.document(audit_id).set(audit_data)

        return self.get_policy_version(tenant_id, new_version_num)  # type: ignore[return-value]

    def activate_version(
        self,
        tenant_id: str,
        version: int,
        actor_id: str = "system",
        reason: str = "Policy activation",
        request_id: str = "req_unknown",
    ) -> MerchantPolicyVersion:
        now = datetime.now(timezone.utc)
        target_doc = self.policies_col.document(f"{tenant_id}_v{version}").get()
        if not target_doc.exists:
            target_docs = self.policies_col.where("tenant_id", "==", tenant_id).where("version", "==", version).get()
            if not target_docs:
                raise ValueError(f"Policy version {version} not found for tenant '{tenant_id}'")
            target_data = target_docs[0].to_dict()
            doc_id = target_docs[0].id
        else:
            target_data = target_doc.to_dict()
            doc_id = target_doc.id

        if target_data.get("status") == PolicyVersionStatus.ACTIVE.value:
            return self.get_policy_version(tenant_id, version)  # type: ignore[return-value]

        prev_docs = self.policies_col.where("tenant_id", "==", tenant_id).where("status", "==", PolicyVersionStatus.ACTIVE.value).get()
        prev_version_num: int | None = None
        for p_doc in prev_docs:
            p_dict = p_doc.to_dict()
            if int(p_dict.get("version", 0)) != version:
                prev_version_num = int(p_dict["version"])
                self.policies_col.document(p_doc.id).update({
                    "status": PolicyVersionStatus.SUPERSEDED.value,
                    "deactivated_at": format_dt(now),
                })

        self.policies_col.document(doc_id).update({
            "status": PolicyVersionStatus.ACTIVE.value,
            "activated_at": format_dt(now),
        })

        audit_id = f"aud_act_{version}_{now.timestamp()}"
        audit_data = {
            "audit_id": audit_id,
            "tenant_id": tenant_id,
            "policy_id": target_data["policy_id"],
            "policy_version": version,
            "action": PolicyAuditAction.ACTIVATED.value,
            "actor_id": actor_id,
            "previous_version": prev_version_num,
            "new_version": version,
            "configuration_hash": target_data["configuration_hash"],
            "timestamp": format_dt(now),
            "reason": reason,
            "request_id": request_id,
        }
        self.audit_col.document(audit_id).set(audit_data)

        return self.get_policy_version(tenant_id, version)  # type: ignore[return-value]

    def rollback_to_version(
        self,
        tenant_id: str,
        target_version: int,
        actor_id: str = "system",
        reason: str = "Policy rollback",
        request_id: str = "req_unknown",
    ) -> MerchantPolicyVersion:
        historical_target = self.get_policy_version(tenant_id, target_version)
        if not historical_target:
            raise ValueError(f"Rollback failed: Historical version {target_version} does not exist for tenant '{tenant_id}'")

        latest = self.get_latest_version_number(tenant_id)
        new_version_num = latest + 1
        now = datetime.now(timezone.utc)
        cfg_hash = historical_target.configuration_hash

        doc_id = f"{tenant_id}_v{new_version_num}"
        rec_data = {
            "policy_id": historical_target.policy_id,
            "tenant_id": tenant_id,
            "version": new_version_num,
            "status": PolicyVersionStatus.ACTIVE.value,
            "configuration_json": historical_target.configuration_json,
            "configuration_hash": cfg_hash,
            "created_by": actor_id,
            "created_at": format_dt(now),
            "activated_at": format_dt(now),
            "parent_version": latest,
            "rollback_source_version": target_version,
        }
        self.policies_col.document(doc_id).set(rec_data)

        active_docs = self.policies_col.where("tenant_id", "==", tenant_id).where("status", "==", PolicyVersionStatus.ACTIVE.value).get()
        prev_version_num: int | None = None
        for a_doc in active_docs:
            if a_doc.id != doc_id:
                prev_version_num = int(a_doc.to_dict().get("version", 0))
                self.policies_col.document(a_doc.id).update({
                    "status": PolicyVersionStatus.SUPERSEDED.value,
                    "deactivated_at": format_dt(now),
                })

        audit_id = f"aud_rb_{new_version_num}_{now.timestamp()}"
        audit_data = {
            "audit_id": audit_id,
            "tenant_id": tenant_id,
            "policy_id": historical_target.policy_id,
            "policy_version": new_version_num,
            "action": PolicyAuditAction.ROLLED_BACK.value,
            "actor_id": actor_id,
            "previous_version": prev_version_num,
            "new_version": new_version_num,
            "configuration_hash": cfg_hash,
            "timestamp": format_dt(now),
            "reason": f"{reason} (rolled back to version {target_version})",
            "request_id": request_id,
        }
        self.audit_col.document(audit_id).set(audit_data)

        return self.get_policy_version(tenant_id, new_version_num)  # type: ignore[return-value]

    def list_audit_logs(self, tenant_id: str) -> list[PolicyAuditLog]:
        docs = self.audit_col.where("tenant_id", "==", tenant_id).get()
        data_list = [d.to_dict() for d in docs]
        data_list.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return [
            PolicyAuditLog(
                audit_id=str(r["audit_id"]),
                tenant_id=str(r["tenant_id"]),
                policy_id=str(r["policy_id"]),
                policy_version=int(r["policy_version"]),
                action=PolicyAuditAction(str(r["action"])),
                actor_id=str(r["actor_id"]),
                previous_version=int(r["previous_version"]) if r.get("previous_version") else None,
                new_version=int(r["new_version"]) if r.get("new_version") else None,
                configuration_hash=str(r["configuration_hash"]),
                timestamp=parse_dt(r["timestamp"]),
                reason=str(r["reason"]),
                request_id=str(r["request_id"]),
            )
            for r in data_list
        ]


class FirestoreDecisionRepository:
    """Firestore Repository for DecisionTrace records."""

    def __init__(self, db: Any = None) -> None:
        self.db = db or get_firestore_client()
        self.collection = self.db.collection("decision_traces")

    def save_trace(self, trace_data: dict[str, Any]) -> DecisionTraceRecord:
        data = dict(trace_data)
        did = data["decision_id"]
        if "created_at" in data:
            data["created_at"] = format_dt(parse_dt(data["created_at"]))
        else:
            data["created_at"] = format_dt(datetime.now(timezone.utc))

        doc_ref = self.collection.document(did)
        doc = doc_ref.get()
        if doc.exists:
            existing = doc.to_dict()
            existing.update(data)
            doc_ref.set(existing)
            merged = existing
        else:
            doc_ref.set(data)
            merged = data

        return DecisionTraceRecord(
            decision_id=merged.get("decision_id", did),
            tenant_id=merged.get("tenant_id", "default_tenant"),
            policy_id=merged.get("policy_id", "default_policy"),
            policy_version=merged.get("policy_version", 1),
            policy_hash=merged.get("policy_hash", "default_hash"),
            opportunity_id=merged.get("opportunity_id", "opp_default"),
            merchant_id=merged.get("merchant_id", "mer_default"),
            customer_id=merged.get("customer_id", "cust_default"),
            payment_id=merged.get("payment_id", "pay_default"),
            status=merged.get("status", "INITIATED"),
            root_cause=merged.get("root_cause"),
            selected_action_type=merged.get("selected_action_type"),
            policy_decision=merged.get("policy_decision", "INITIATED"),
            policy_token_id=merged.get("policy_token_id"),
            input_state_json=merged.get("input_state_json", {}),
            trace_data_json=merged.get("trace_data_json", {}),
            created_at=parse_dt(merged.get("created_at")),
        )

    def get_by_id(self, decision_id: str) -> DecisionTraceRecord | None:
        doc = self.collection.document(decision_id).get()
        if not doc.exists:
            return None
        d = doc.to_dict()
        return DecisionTraceRecord(
            decision_id=d.get("decision_id", decision_id),
            tenant_id=d.get("tenant_id", "default_tenant"),
            policy_id=d.get("policy_id", "default_policy"),
            policy_version=d.get("policy_version", 1),
            policy_hash=d.get("policy_hash", "default_hash"),
            opportunity_id=d.get("opportunity_id", "opp_default"),
            merchant_id=d.get("merchant_id", "mer_default"),
            customer_id=d.get("customer_id", "cust_default"),
            payment_id=d.get("payment_id", "pay_default"),
            status=d.get("status", "INITIATED"),
            root_cause=d.get("root_cause"),
            selected_action_type=d.get("selected_action_type"),
            policy_decision=d.get("policy_decision", "INITIATED"),
            policy_token_id=d.get("policy_token_id"),
            input_state_json=d.get("input_state_json", {}),
            trace_data_json=d.get("trace_data_json", {}),
            created_at=parse_dt(d.get("created_at")),
        )

    def get_latest_by_payment(self, payment_id: str) -> DecisionTraceRecord | None:
        docs = self.collection.where("payment_id", "==", payment_id).get()
        if not docs:
            return None
        data_list = [d.to_dict() for d in docs]
        data_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        d = data_list[0]
        return DecisionTraceRecord(
            decision_id=d.get("decision_id"),
            tenant_id=d.get("tenant_id", "default_tenant"),
            policy_id=d.get("policy_id", "default_policy"),
            policy_version=d.get("policy_version", 1),
            policy_hash=d.get("policy_hash", "default_hash"),
            opportunity_id=d.get("opportunity_id", "opp_default"),
            merchant_id=d.get("merchant_id", "mer_default"),
            customer_id=d.get("customer_id", "cust_default"),
            payment_id=d.get("payment_id", "pay_default"),
            status=d.get("status", "INITIATED"),
            root_cause=d.get("root_cause"),
            selected_action_type=d.get("selected_action_type"),
            policy_decision=d.get("policy_decision", "INITIATED"),
            policy_token_id=d.get("policy_token_id"),
            input_state_json=d.get("input_state_json", {}),
            trace_data_json=d.get("trace_data_json", {}),
            created_at=parse_dt(d.get("created_at")),
        )

    def list_traces(
        self,
        status: str | None = None,
        payment_id: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[DecisionTraceRecord], int]:
        docs = [d.to_dict() for d in self.collection.get()]
        filtered: list[dict[str, Any]] = []

        for d in docs:
            if status and d.get("status") != status:
                continue
            if payment_id and d.get("payment_id") != payment_id:
                continue
            filtered.append(d)

        filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = filtered[start:end]

        records = [
            DecisionTraceRecord(
                decision_id=d.get("decision_id"),
                tenant_id=d.get("tenant_id", "default_tenant"),
                policy_id=d.get("policy_id", "default_policy"),
                policy_version=d.get("policy_version", 1),
                policy_hash=d.get("policy_hash", "default_hash"),
                opportunity_id=d.get("opportunity_id", "opp_default"),
                merchant_id=d.get("merchant_id", "mer_default"),
                customer_id=d.get("customer_id", "cust_default"),
                payment_id=d.get("payment_id", "pay_default"),
                status=d.get("status", "INITIATED"),
                root_cause=d.get("root_cause"),
                selected_action_type=d.get("selected_action_type"),
                policy_decision=d.get("policy_decision", "INITIATED"),
                policy_token_id=d.get("policy_token_id"),
                input_state_json=d.get("input_state_json", {}),
                trace_data_json=d.get("trace_data_json", {}),
                created_at=parse_dt(d.get("created_at")),
            )
            for d in page_items
        ]
        return records, total


class FirestoreJobRepository:
    """Firestore Repository for background recovery jobs."""

    def __init__(self, db: Any = None) -> None:
        self.db = db or get_firestore_client()
        self.collection = self.db.collection("background_jobs")

    def create_job(self, job_id: str, event_id: str, payment_id: str, payload: dict[str, Any]) -> BackgroundJobRecord:
        now = datetime.now(timezone.utc)
        data = {
            "job_id": job_id,
            "tenant_id": payload.get("tenant_id", "default_tenant"),
            "event_id": event_id,
            "payment_id": payment_id,
            "status": "QUEUED",
            "attempt_count": 0,
            "max_attempts": 3,
            "payload_json": payload,
            "next_attempt_at": format_dt(now),
            "created_at": format_dt(now),
            "updated_at": format_dt(now),
        }
        self.collection.document(job_id).set(data)
        return BackgroundJobRecord(
            job_id=job_id,
            tenant_id=data["tenant_id"],
            event_id=event_id,
            payment_id=payment_id,
            status="QUEUED",
            attempt_count=0,
            max_attempts=3,
            payload_json=payload,
            next_attempt_at=now,
            created_at=now,
            updated_at=now,
        )

    def fetch_next_queued_job(self) -> BackgroundJobRecord | None:
        now = datetime.now(timezone.utc)
        now_str = format_dt(now)
        docs = [d.to_dict() for d in self.collection.get()]
        pending = [
            d for d in docs
            if d.get("status") in ("QUEUED", "RETRYING")
            and (d.get("next_attempt_at") is None or d.get("next_attempt_at", "") <= now_str)
        ]
        if not pending:
            return None

        pending.sort(key=lambda x: x.get("created_at", ""))
        target = pending[0]
        job_id = target["job_id"]
        attempts = target.get("attempt_count", 0) + 1

        self.collection.document(job_id).update({
            "status": "PROCESSING",
            "attempt_count": attempts,
            "updated_at": format_dt(now),
        })

        target["status"] = "PROCESSING"
        target["attempt_count"] = attempts

        return BackgroundJobRecord(
            job_id=target["job_id"],
            tenant_id=target.get("tenant_id", "default_tenant"),
            event_id=target["event_id"],
            payment_id=target["payment_id"],
            status="PROCESSING",
            attempt_count=attempts,
            max_attempts=target.get("max_attempts", 3),
            failure_reason=target.get("failure_reason"),
            payload_json=target.get("payload_json", {}),
            next_attempt_at=parse_dt(target.get("next_attempt_at")),
            created_at=parse_dt(target.get("created_at")),
            updated_at=now,
        )

    def mark_completed(self, job_id: str, trace_id: str | None = None) -> BackgroundJobRecord | None:
        doc_ref = self.collection.document(job_id)
        doc = doc_ref.get()
        if not doc.exists:
            return None
        now = datetime.now(timezone.utc)
        updates = {"status": "COMPLETED", "updated_at": format_dt(now)}
        if trace_id:
            updates["trace_id"] = trace_id
        doc_ref.update(updates)
        d = doc.to_dict()
        d.update(updates)
        return BackgroundJobRecord(
            job_id=d["job_id"],
            tenant_id=d.get("tenant_id", "default_tenant"),
            event_id=d["event_id"],
            payment_id=d["payment_id"],
            trace_id=d.get("trace_id"),
            status="COMPLETED",
            attempt_count=d.get("attempt_count", 0),
            max_attempts=d.get("max_attempts", 3),
            failure_reason=d.get("failure_reason"),
            payload_json=d.get("payload_json", {}),
            created_at=parse_dt(d.get("created_at")),
            updated_at=now,
        )

    def mark_failed(self, job_id: str, reason: str, can_retry: bool = True) -> BackgroundJobRecord | None:
        doc_ref = self.collection.document(job_id)
        doc = doc_ref.get()
        if not doc.exists:
            return None
        d = doc.to_dict()
        now = datetime.now(timezone.utc)
        attempts = d.get("attempt_count", 1)
        max_att = d.get("max_attempts", 3)
        new_status = "RETRYING" if can_retry and attempts < max_att else "DEAD_LETTER"

        updates = {
            "status": new_status,
            "failure_reason": reason,
            "updated_at": format_dt(now),
        }
        doc_ref.update(updates)
        d.update(updates)
        return BackgroundJobRecord(
            job_id=d["job_id"],
            tenant_id=d.get("tenant_id", "default_tenant"),
            event_id=d["event_id"],
            payment_id=d["payment_id"],
            status=new_status,
            attempt_count=attempts,
            max_attempts=max_att,
            failure_reason=reason,
            payload_json=d.get("payload_json", {}),
            created_at=parse_dt(d.get("created_at")),
            updated_at=now,
        )


class FirestoreAPIKeyRepository:
    """Firestore Repository managing API keys and users."""

    def __init__(self, db: Any = None) -> None:
        self.db = db or get_firestore_client()
        self.keys_col = self.db.collection("user_api_keys")
        self.users_col = self.db.collection("users")

    @staticmethod
    def hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def generate_api_key(
        self,
        tenant_id: str,
        user_id: str,
        name: str,
        role: str = "OPERATIONS_READ",
        expires_at: datetime | None = None,
    ) -> tuple[str, UserAPIKeyRecord]:
        prefix = f"rvn_{role.lower()[:4]}_"
        random_part = secrets.token_urlsafe(24)
        raw_key = f"{prefix}{random_part}"
        key_hash = self.hash_key(raw_key)
        key_id = f"key_{secrets.token_hex(8)}"
        now = datetime.now(timezone.utc)

        rec_data = {
            "key_id": key_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "name": name,
            "key_prefix": prefix[:16],
            "key_hash": key_hash,
            "role": role,
            "revoked": False,
            "expires_at": format_dt(expires_at),
            "created_at": format_dt(now),
        }
        self.keys_col.document(key_id).set(rec_data)

        rec = UserAPIKeyRecord(
            key_id=key_id,
            user_id=user_id,
            tenant_id=tenant_id,
            name=name,
            key_prefix=prefix[:16],
            key_hash=key_hash,
            role=role,
            revoked=False,
            expires_at=expires_at,
            created_at=now,
        )
        return raw_key, rec

    def validate_api_key(self, raw_key: str) -> UserAPIKeyRecord | None:
        if not raw_key:
            return None
        target_hash = self.hash_key(raw_key)
        docs = self.keys_col.where("key_hash", "==", target_hash).where("revoked", "==", False).get()
        if not docs:
            return None

        d = docs[0].to_dict()
        exp = parse_dt(d.get("expires_at")) if d.get("expires_at") else None
        if exp and exp < datetime.now(timezone.utc):
            return None

        return UserAPIKeyRecord(
            key_id=d["key_id"],
            user_id=d["user_id"],
            tenant_id=d["tenant_id"],
            name=d["name"],
            key_prefix=d["key_prefix"],
            key_hash=d["key_hash"],
            role=d["role"],
            revoked=d.get("revoked", False),
            expires_at=exp,
            created_at=parse_dt(d["created_at"]),
        )

    def revoke_api_key(self, key_id: str) -> bool:
        doc_ref = self.keys_col.document(key_id)
        doc = doc_ref.get()
        if not doc.exists:
            return False
        doc_ref.update({"revoked": True})
        return True

    def create_user(
        self,
        tenant_id: str,
        email: str,
        password: str,
        role: str = "OPERATIONS_READ",
    ) -> UserRecord:
        user_id = f"usr_{secrets.token_hex(8)}"
        pwd_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        now = datetime.now(timezone.utc)

        data = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "email": email,
            "hashed_password": pwd_hash,
            "role": role,
            "is_active": True,
            "created_at": format_dt(now),
        }
        self.users_col.document(user_id).set(data)
        return UserRecord(
            user_id=user_id,
            tenant_id=tenant_id,
            email=email,
            hashed_password=pwd_hash,
            role=role,
            is_active=True,
            created_at=now,
        )


class FirestoreToolExecutionRepository:
    """Firestore Repository for Tool Execution audit logs."""

    def __init__(self, db: Any = None) -> None:
        self.db = db or get_firestore_client()
        self.collection = self.db.collection("tool_executions")

    def save_execution(self, execution_data: dict[str, Any]) -> ToolExecutionRecord:
        data = dict(execution_data)
        eid = data["execution_id"]
        now = datetime.now(timezone.utc)
        data["executed_at"] = format_dt(parse_dt(data.get("executed_at", now)))

        doc_ref = self.collection.document(eid)
        doc_ref.set(data)
        return ToolExecutionRecord(
            execution_id=eid,
            tenant_id=data.get("tenant_id", "default_tenant"),
            tool_name=data["tool_name"],
            action_id=data["action_id"],
            payment_id=data["payment_id"],
            status=data["status"],
            policy_token_id=data.get("policy_token_id"),
            executed_at=parse_dt(data["executed_at"]),
            parameters_json=data.get("parameters_json", data.get("parameters", {})),
            result_json=data.get("result_json", data.get("result", {})),
        )

    def list_executions(
        self,
        payment_id: str | None = None,
        tool_name: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[ToolExecutionRecord], int]:
        docs = [d.to_dict() for d in self.collection.get()]
        filtered: list[dict[str, Any]] = []

        for d in docs:
            if payment_id and d.get("payment_id") != payment_id:
                continue
            if tool_name and d.get("tool_name") != tool_name:
                continue
            if status and d.get("status") != status:
                continue
            filtered.append(d)

        filtered.sort(key=lambda x: x.get("executed_at", ""), reverse=True)
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = filtered[start:end]

        records = [
            ToolExecutionRecord(
                execution_id=d["execution_id"],
                tenant_id=d.get("tenant_id", "default_tenant"),
                tool_name=d["tool_name"],
                action_id=d["action_id"],
                payment_id=d["payment_id"],
                status=d["status"],
                policy_token_id=d.get("policy_token_id"),
                executed_at=parse_dt(d["executed_at"]),
                parameters_json=d.get("parameters_json", d.get("parameters", {})),
                result_json=d.get("result_json", d.get("result", {})),
            )
            for d in page_items
        ]
        return records, total


class FirestoreVerificationRepository:
    """Firestore Repository for Verification outcomes."""

    def __init__(self, db: Any = None) -> None:
        self.db = db or get_firestore_client()
        self.collection = self.db.collection("verifications")

    def save_verification(self, verification_data: dict[str, Any]) -> VerificationRecord:
        data = dict(verification_data)
        now = datetime.now(timezone.utc)
        data["verified_at"] = format_dt(parse_dt(data.get("verified_at", now)))
        doc_id = f"{data['payment_id']}_{data['action_id']}"

        self.collection.document(doc_id).set(data)
        return VerificationRecord(
            tenant_id=data.get("tenant_id", "default_tenant"),
            payment_id=data["payment_id"],
            action_id=data["action_id"],
            trace_id=data.get("trace_id"),
            recovery_type=data["recovery_type"],
            is_recovered=data["is_recovered"],
            recovered_amount_minor=data.get("recovered_amount_minor", 0),
            verified_at=parse_dt(data["verified_at"]),
        )

    def list_verifications(
        self,
        payment_id: str | None = None,
        recovery_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[VerificationRecord], int]:
        docs = [d.to_dict() for d in self.collection.get()]
        filtered: list[dict[str, Any]] = []

        for d in docs:
            if payment_id and d.get("payment_id") != payment_id:
                continue
            if recovery_type and d.get("recovery_type") != recovery_type:
                continue
            filtered.append(d)

        filtered.sort(key=lambda x: x.get("verified_at", ""), reverse=True)
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = filtered[start:end]

        records = [
            VerificationRecord(
                tenant_id=d.get("tenant_id", "default_tenant"),
                payment_id=d["payment_id"],
                action_id=d["action_id"],
                trace_id=d.get("trace_id"),
                recovery_type=d["recovery_type"],
                is_recovered=d["is_recovered"],
                recovered_amount_minor=d.get("recovered_amount_minor", 0),
                verified_at=parse_dt(d["verified_at"]),
            )
            for d in page_items
        ]
        return records, total


class FirestoreWebhookIngestionRepository:
    """Firestore Repository for Webhook Ingestion deduplication."""

    def __init__(self, db: Any = None) -> None:
        self.db = db or get_firestore_client()
        self.collection = self.db.collection("webhook_ingestions")

    def save_webhook(self, webhook_data: dict[str, Any]) -> WebhookRecord:
        data = dict(webhook_data)
        sig_hash = data["signature_hash"]
        now = datetime.now(timezone.utc)
        data["received_at"] = format_dt(parse_dt(data.get("received_at", now)))

        existing_docs = self.collection.where("signature_hash", "==", sig_hash).get()
        if existing_docs:
            d = existing_docs[0].to_dict()
            return WebhookRecord(
                tenant_id=d.get("tenant_id", "default_tenant"),
                webhook_id=d["webhook_id"],
                event_id=d["event_id"],
                signature_hash=d["signature_hash"],
                payload_hash=d["payload_hash"],
                received_at=parse_dt(d["received_at"]),
                processed=d.get("processed", False),
            )

        doc_id = data.get("webhook_id") or f"whk_{int(now.timestamp() * 1000)}"
        self.collection.document(doc_id).set(data)
        return WebhookRecord(
            tenant_id=data.get("tenant_id", "default_tenant"),
            webhook_id=doc_id,
            event_id=data["event_id"],
            signature_hash=sig_hash,
            payload_hash=data["payload_hash"],
            received_at=parse_dt(data["received_at"]),
            processed=data.get("processed", False),
        )
