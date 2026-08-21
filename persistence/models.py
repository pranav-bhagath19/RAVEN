"""
RAVEN Production SQLAlchemy Database Models

Defines persistent ORM schemas for Tenants, Payments, Financial Events, Decision Traces,
Merchant Policies, Policy Audit Logs, Tool Executions, Verifications, Webhooks, Telemetry, Background Jobs,
Adaptive Outcomes, Model Registry, Drift Reports, and Optimization Reports.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from persistence.database import Base


def utc_now() -> datetime:
    """Returns current UTC timestamp."""
    return datetime.now(timezone.utc)


class TenantRecord(Base):
    """Persistent Tenant entity table."""

    __tablename__ = "tenants"

    tenant_id = Column(String(64), primary_key=True, index=True)
    merchant_id = Column(String(64), nullable=False, unique=True, index=True)
    name = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class PaymentRecord(Base):
    """Persistent Payment entity table."""

    __tablename__ = "payments"

    payment_id = Column(String(64), primary_key=True, index=True)
    tenant_id = Column(String(64), nullable=False, default="default_tenant", index=True)
    order_id = Column(String(64), nullable=True, index=True)
    merchant_id = Column(String(64), nullable=False, index=True)
    customer_id = Column(String(64), nullable=False, index=True)
    amount_minor = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    status = Column(String(32), nullable=False, index=True)
    attempts_count = Column(Integer, nullable=False, default=0)
    error_code = Column(String(64), nullable=True, index=True)
    error_description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        Index("idx_payments_tenant_payment", "tenant_id", "payment_id"),
        Index("idx_payments_tenant_created", "tenant_id", "created_at"),
    )


class FinancialEventRecord(Base):
    """Persistent append-only Financial Event log table."""

    __tablename__ = "financial_events"

    event_id = Column(String(64), primary_key=True, index=True)
    tenant_id = Column(String(64), nullable=False, default="default_tenant", index=True)
    event_hash = Column(String(64), nullable=False, unique=True, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(64), nullable=False, index=True)  # payment_id
    merchant_id = Column(String(64), nullable=False, index=True)
    amount_minor = Column(Integer, nullable=True)
    currency = Column(String(3), nullable=False, default="INR")
    sequence_number = Column(Integer, nullable=False, default=0)
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True)
    received_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    payload_json = Column(JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("idx_events_entity_occurred", "entity_id", "occurred_at"),
        Index("idx_events_tenant_event", "tenant_id", "event_id"),
    )


class WebhookRecord(Base):
    """Persistent Razorpay Webhook Ingestion audit & deduplication table."""

    __tablename__ = "webhook_ingestions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(64), nullable=False, default="default_tenant", index=True)
    webhook_id = Column(String(64), nullable=False, index=True)
    event_id = Column(String(64), nullable=False, index=True)
    signature_hash = Column(String(64), nullable=False, unique=True, index=True)
    payload_hash = Column(String(64), nullable=False, index=True)
    received_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    processed = Column(Boolean, nullable=False, default=False)


class DecisionTraceRecord(Base):
    """Persistent DecisionTrace lifecycle lineage table."""

    __tablename__ = "decision_traces"

    decision_id = Column(String(64), primary_key=True, index=True)
    tenant_id = Column(String(64), nullable=False, default="default_tenant", index=True)
    policy_id = Column(String(64), nullable=False, default="default_policy", index=True)
    policy_version = Column(Integer, nullable=False, default=1)
    policy_hash = Column(String(64), nullable=False, default="default_hash")
    opportunity_id = Column(String(64), nullable=False, index=True)
    merchant_id = Column(String(64), nullable=False, index=True)
    customer_id = Column(String(64), nullable=False, index=True)
    payment_id = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True)
    root_cause = Column(String(64), nullable=True)
    selected_action_type = Column(String(64), nullable=True)
    policy_decision = Column(String(32), nullable=False, default="INITIATED")
    policy_token_id = Column(String(64), nullable=True)
    input_state_json = Column(JSON, nullable=False, default=dict)
    trace_data_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        Index("idx_traces_tenant_decision", "tenant_id", "decision_id"),
        Index("idx_traces_tenant_policy_ver", "tenant_id", "policy_version"),
    )


class MerchantPolicyRecord(Base):
    """Persistent Merchant Policy Version table."""

    __tablename__ = "merchant_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_id = Column(String(64), nullable=False, index=True)
    tenant_id = Column(String(64), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    status = Column(String(32), nullable=False, index=True, default="DRAFT")
    configuration_json = Column(JSON, nullable=False, default=dict)
    configuration_hash = Column(String(64), nullable=False, index=True)
    created_by = Column(String(64), nullable=False, default="system")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    parent_version = Column(Integer, nullable=True)
    rollback_source_version = Column(Integer, nullable=True)

    __table_args__ = (
        Index("idx_policies_tenant_version", "tenant_id", "version", unique=True),
        Index("idx_policies_tenant_status", "tenant_id", "status"),
    )


class PolicyAuditLogRecord(Base):
    """Persistent Policy Audit Log table."""

    __tablename__ = "policy_audit_logs"

    audit_id = Column(String(64), primary_key=True, index=True)
    tenant_id = Column(String(64), nullable=False, index=True)
    policy_id = Column(String(64), nullable=False, index=True)
    policy_version = Column(Integer, nullable=False)
    action = Column(String(32), nullable=False, index=True)
    actor_id = Column(String(64), nullable=False)
    previous_version = Column(Integer, nullable=True)
    new_version = Column(Integer, nullable=True)
    configuration_hash = Column(String(64), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    reason = Column(Text, nullable=False)
    request_id = Column(String(64), nullable=False, default="req_unknown")

    __table_args__ = (
        Index("idx_policy_audit_tenant", "tenant_id", "timestamp"),
    )


class ToolExecutionRecord(Base):
    """Persistent ToolExecutor side-effect audit log table."""

    __tablename__ = "tool_executions"

    execution_id = Column(String(64), primary_key=True, index=True)
    tenant_id = Column(String(64), nullable=False, default="default_tenant", index=True)
    tool_name = Column(String(64), nullable=False, index=True)
    action_id = Column(String(64), nullable=False, index=True)
    payment_id = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True)
    policy_token_id = Column(String(64), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    parameters_json = Column(JSON, nullable=False, default=dict)
    result_json = Column(JSON, nullable=False, default=dict)


class VerificationRecord(Base):
    """Persistent Verification outcome table."""

    __tablename__ = "verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(64), nullable=False, default="default_tenant", index=True)
    payment_id = Column(String(64), nullable=False, index=True)
    action_id = Column(String(64), nullable=False, index=True)
    trace_id = Column(String(64), nullable=True, index=True)
    recovery_type = Column(String(64), nullable=False, index=True)
    is_recovered = Column(Boolean, nullable=False)
    recovered_amount_minor = Column(Integer, nullable=False, default=0)
    verified_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class TelemetryRecord(Base):
    """Persistent PII-sanitized Observability Telemetry table."""

    __tablename__ = "observability_telemetry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(64), nullable=False, default="default_tenant", index=True)
    trace_id = Column(String(64), nullable=False, index=True)
    agent_name = Column(String(64), nullable=False, index=True)
    provider = Column(String(64), nullable=False)
    model = Column(String(64), nullable=False)
    prompt_version = Column(String(32), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=False)
    latency_ms = Column(Float, nullable=False)
    success = Column(Boolean, nullable=False)
    failure_reason = Column(Text, nullable=True)
    reasoning_mode = Column(String(32), nullable=False)
    input_summary = Column(Text, nullable=False)
    output_summary = Column(Text, nullable=False)


class BackgroundJobRecord(Base):
    """Persistent Background Job queue table."""

    __tablename__ = "background_jobs"

    job_id = Column(String(64), primary_key=True, index=True)
    tenant_id = Column(String(64), nullable=False, default="default_tenant", index=True)
    event_id = Column(String(64), nullable=False, index=True)
    payment_id = Column(String(64), nullable=False, index=True)
    trace_id = Column(String(64), nullable=True, index=True)
    status = Column(String(32), nullable=False, index=True, default="QUEUED")
    attempt_count = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    failure_reason = Column(Text, nullable=True)
    payload_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
    next_attempt_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)


class AdaptiveOutcomeRecordModel(Base):
    """Persistent Adaptive Outcome record table."""

    __tablename__ = "adaptive_outcomes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(64), nullable=False, index=True)
    payment_id = Column(String(64), nullable=False, index=True)
    decision_id = Column(String(64), nullable=False, index=True)
    action_type = Column(String(64), nullable=False)
    amount_minor = Column(Integer, nullable=False)
    outcome = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class ModelRegistryRecord(Base):
    """Persistent Model Registry table."""

    __tablename__ = "model_registry"

    model_version = Column(String(64), primary_key=True, index=True)
    model_type = Column(String(64), nullable=False)
    feature_schema_version = Column(String(32), nullable=False)
    training_dataset_hash = Column(String(64), nullable=False)
    artifact_hash = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, index=True)
    metrics_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
