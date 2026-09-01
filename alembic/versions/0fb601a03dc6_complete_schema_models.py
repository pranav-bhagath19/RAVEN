"""complete_schema_models

Revision ID: 0fb601a03dc6
Revises: 3a3310de7765
Create Date: 2026-09-01 01:18:37.220956

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0fb601a03dc6'
down_revision: Union[str, None] = '3a3310de7765'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check table existence to be safe on existing DBs
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'tenants' not in existing_tables:
        op.create_table(
            'tenants',
            sa.Column('tenant_id', sa.String(length=64), primary_key=True),
            sa.Column('merchant_id', sa.String(length=64), nullable=False, unique=True),
            sa.Column('name', sa.String(length=128), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )

    if 'payments' not in existing_tables:
        op.create_table(
            'payments',
            sa.Column('payment_id', sa.String(length=64), primary_key=True),
            sa.Column('tenant_id', sa.String(length=64), nullable=False),
            sa.Column('order_id', sa.String(length=64), nullable=True),
            sa.Column('merchant_id', sa.String(length=64), nullable=False),
            sa.Column('customer_id', sa.String(length=64), nullable=False),
            sa.Column('amount_minor', sa.Integer(), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False),
            sa.Column('attempts_count', sa.Integer(), nullable=False),
            sa.Column('error_code', sa.String(length=64), nullable=True),
            sa.Column('error_description', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )

    if 'financial_events' not in existing_tables:
        op.create_table(
            'financial_events',
            sa.Column('event_id', sa.String(length=64), primary_key=True),
            sa.Column('tenant_id', sa.String(length=64), nullable=False),
            sa.Column('event_hash', sa.String(length=64), nullable=False, unique=True),
            sa.Column('event_type', sa.String(length=64), nullable=False),
            sa.Column('entity_id', sa.String(length=64), nullable=False),
            sa.Column('merchant_id', sa.String(length=64), nullable=False),
            sa.Column('amount_minor', sa.Integer(), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=False),
            sa.Column('sequence_number', sa.Integer(), nullable=False),
            sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('payload_json', sa.JSON(), nullable=False),
        )

    if 'webhook_ingestions' not in existing_tables:
        op.create_table(
            'webhook_ingestions',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('tenant_id', sa.String(length=64), nullable=False),
            sa.Column('webhook_id', sa.String(length=64), nullable=False),
            sa.Column('event_id', sa.String(length=64), nullable=False),
            sa.Column('signature_hash', sa.String(length=64), nullable=False, unique=True),
            sa.Column('payload_hash', sa.String(length=64), nullable=False),
            sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('processed', sa.Boolean(), nullable=False),
        )

    if 'decision_traces' not in existing_tables:
        op.create_table(
            'decision_traces',
            sa.Column('decision_id', sa.String(length=64), primary_key=True),
            sa.Column('tenant_id', sa.String(length=64), nullable=False),
            sa.Column('policy_id', sa.String(length=64), nullable=False),
            sa.Column('policy_version', sa.Integer(), nullable=False),
            sa.Column('policy_hash', sa.String(length=64), nullable=False),
            sa.Column('opportunity_id', sa.String(length=64), nullable=False),
            sa.Column('merchant_id', sa.String(length=64), nullable=False),
            sa.Column('customer_id', sa.String(length=64), nullable=False),
            sa.Column('payment_id', sa.String(length=64), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False),
            sa.Column('root_cause', sa.String(length=64), nullable=True),
            sa.Column('selected_action_type', sa.String(length=64), nullable=True),
            sa.Column('policy_decision', sa.String(length=32), nullable=False),
            sa.Column('policy_token_id', sa.String(length=64), nullable=True),
            sa.Column('input_state_json', sa.JSON(), nullable=False),
            sa.Column('trace_data_json', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        )

    if 'merchant_policies' not in existing_tables:
        op.create_table(
            'merchant_policies',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('policy_id', sa.String(length=64), nullable=False),
            sa.Column('tenant_id', sa.String(length=64), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False),
            sa.Column('configuration_json', sa.JSON(), nullable=False),
            sa.Column('configuration_hash', sa.String(length=64), nullable=False),
            sa.Column('created_by', sa.String(length=64), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('deactivated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('parent_version', sa.Integer(), nullable=True),
            sa.Column('rollback_source_version', sa.Integer(), nullable=True),
        )

    if 'policy_audit_logs' not in existing_tables:
        op.create_table(
            'policy_audit_logs',
            sa.Column('audit_id', sa.String(length=64), primary_key=True),
            sa.Column('tenant_id', sa.String(length=64), nullable=False),
            sa.Column('policy_id', sa.String(length=64), nullable=False),
            sa.Column('policy_version', sa.Integer(), nullable=False),
            sa.Column('action', sa.String(length=32), nullable=False),
            sa.Column('actor_id', sa.String(length=64), nullable=False),
            sa.Column('previous_version', sa.Integer(), nullable=True),
            sa.Column('new_version', sa.Integer(), nullable=True),
            sa.Column('configuration_hash', sa.String(length=64), nullable=False),
            sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
            sa.Column('reason', sa.Text(), nullable=False),
            sa.Column('request_id', sa.String(length=64), nullable=False),
        )

    if 'tool_executions' not in existing_tables:
        op.create_table(
            'tool_executions',
            sa.Column('execution_id', sa.String(length=64), primary_key=True),
            sa.Column('tenant_id', sa.String(length=64), nullable=False),
            sa.Column('tool_name', sa.String(length=64), nullable=False),
            sa.Column('action_id', sa.String(length=64), nullable=False),
            sa.Column('payment_id', sa.String(length=64), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False),
            sa.Column('policy_token_id', sa.String(length=64), nullable=True),
            sa.Column('executed_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('parameters_json', sa.JSON(), nullable=False),
            sa.Column('result_json', sa.JSON(), nullable=False),
        )

    if 'verifications' not in existing_tables:
        op.create_table(
            'verifications',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('tenant_id', sa.String(length=64), nullable=False),
            sa.Column('payment_id', sa.String(length=64), nullable=False),
            sa.Column('action_id', sa.String(length=64), nullable=False),
            sa.Column('trace_id', sa.String(length=64), nullable=True),
            sa.Column('recovery_type', sa.String(length=64), nullable=False),
            sa.Column('is_recovered', sa.Boolean(), nullable=False),
            sa.Column('recovered_amount_minor', sa.Integer(), nullable=False),
            sa.Column('verified_at', sa.DateTime(timezone=True), nullable=False),
        )

    if 'observability_telemetry' not in existing_tables:
        op.create_table(
            'observability_telemetry',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('tenant_id', sa.String(length=64), nullable=False),
            sa.Column('trace_id', sa.String(length=64), nullable=False),
            sa.Column('agent_name', sa.String(length=64), nullable=False),
            sa.Column('provider', sa.String(length=64), nullable=False),
            sa.Column('model', sa.String(length=64), nullable=False),
            sa.Column('prompt_version', sa.String(length=32), nullable=False),
            sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('latency_ms', sa.Float(), nullable=False),
            sa.Column('success', sa.Boolean(), nullable=False),
            sa.Column('failure_reason', sa.Text(), nullable=True),
            sa.Column('reasoning_mode', sa.String(length=32), nullable=False),
            sa.Column('input_summary', sa.Text(), nullable=False),
            sa.Column('output_summary', sa.Text(), nullable=False),
        )

    if 'background_jobs' not in existing_tables:
        op.create_table(
            'background_jobs',
            sa.Column('job_id', sa.String(length=64), primary_key=True),
            sa.Column('tenant_id', sa.String(length=64), nullable=False),
            sa.Column('event_id', sa.String(length=64), nullable=False),
            sa.Column('payment_id', sa.String(length=64), nullable=False),
            sa.Column('trace_id', sa.String(length=64), nullable=True),
            sa.Column('status', sa.String(length=32), nullable=False),
            sa.Column('attempt_count', sa.Integer(), nullable=False),
            sa.Column('max_attempts', sa.Integer(), nullable=False),
            sa.Column('failure_reason', sa.Text(), nullable=True),
            sa.Column('payload_json', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('next_attempt_at', sa.DateTime(timezone=True), nullable=False),
        )

    if 'adaptive_outcomes' not in existing_tables:
        op.create_table(
            'adaptive_outcomes',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('tenant_id', sa.String(length=64), nullable=False),
            sa.Column('payment_id', sa.String(length=64), nullable=False),
            sa.Column('decision_id', sa.String(length=64), nullable=False),
            sa.Column('action_type', sa.String(length=64), nullable=False),
            sa.Column('amount_minor', sa.Integer(), nullable=False),
            sa.Column('outcome', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        )

    if 'model_registry' not in existing_tables:
        op.create_table(
            'model_registry',
            sa.Column('model_version', sa.String(length=64), primary_key=True),
            sa.Column('model_type', sa.String(length=64), nullable=False),
            sa.Column('feature_schema_version', sa.String(length=32), nullable=False),
            sa.Column('training_dataset_hash', sa.String(length=64), nullable=False),
            sa.Column('artifact_hash', sa.String(length=64), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False),
            sa.Column('metrics_json', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    for table in [
        'model_registry',
        'adaptive_outcomes',
        'background_jobs',
        'observability_telemetry',
        'verifications',
        'tool_executions',
        'policy_audit_logs',
        'merchant_policies',
        'decision_traces',
        'webhook_ingestions',
        'financial_events',
        'payments',
        'tenants',
    ]:
        if table in existing_tables:
            op.drop_table(table)
