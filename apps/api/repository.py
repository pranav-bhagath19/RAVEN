"""
RAVEN Operations Repository Module

Dual-mode data layer querying persistent database models (PostgreSQL / SQLite)
and providing thread-safe in-memory fallback for local demo and offline testing.
"""

import json
import os
import threading
from typing import Any
from agents.observability import LLMObservabilityTelemetry
from domain.entities.decision_trace import DecisionTrace
from domain.entities.financial_event import FinancialEvent
from domain.entities.payment import PaymentStatus
from domain.state.reconstructor import StateReconstructor
from events.ingestion import EventIngestionService
from ml.evaluation.models import BenchmarkReport
from persistence.database import SessionLocal, init_db
from persistence.models import (
    DecisionTraceRecord,
    ToolExecutionRecord,
    VerificationRecord,
)
from policies.rules import get_registered_policies
from tools.executor import ToolExecutor


class OperationsRepository:
    """
    Control plane data repository providing paginated, filtered operational views.
    Integrates persistent DB storage with in-memory execution cache.
    """

    def __init__(
        self,
        ingestion_service: EventIngestionService | None = None,
        tool_executor: ToolExecutor | None = None,
        telemetry: LLMObservabilityTelemetry | None = None,
    ) -> None:
        self._lock = threading.Lock()
        self.ingestion_service = ingestion_service or EventIngestionService()
        self.tool_executor = tool_executor or ToolExecutor()
        self.telemetry = telemetry or LLMObservabilityTelemetry()
        self.reconstructor = StateReconstructor()

        self._traces: dict[str, DecisionTrace] = {}
        self._tool_executions: list[dict[str, Any]] = []
        self._verifications: list[dict[str, Any]] = []

        try:
            init_db()
        except Exception:
            pass

    def record_trace(self, trace: DecisionTrace) -> None:
        """Stores DecisionTrace snapshot in memory and DB."""
        with self._lock:
            self._traces[trace.decision_id] = trace

        try:
            db = SessionLocal()
            rec = db.query(DecisionTraceRecord).filter(DecisionTraceRecord.decision_id == trace.decision_id).first()
            pol_eval = trace.policy_evaluations[-1] if trace.policy_evaluations else {}
            if not rec:
                rec = DecisionTraceRecord(
                    decision_id=trace.decision_id,
                    opportunity_id=trace.recovery_opportunity_id,
                    merchant_id=trace.merchant_id,
                    customer_id=trace.customer_id,
                    payment_id=trace.payment_id,
                    status=str(trace.status),
                    root_cause=trace.root_cause_result.get("primary_root_cause") if trace.root_cause_result else None,
                    selected_action_type=trace.selected_action.get("action_type") if trace.selected_action else None,
                    policy_decision=pol_eval.get("decision_type", "INITIATED"),
                    policy_token_id=trace.policy_token_id,
                    input_state_json=trace.input_state_snapshot,
                    trace_data_json=trace.model_dump(),
                )
                db.add(rec)
                db.commit()
            db.close()
        except Exception:
            pass

    def record_tool_execution(self, record: dict[str, Any]) -> None:
        """Stores tool execution audit log in memory and DB."""
        with self._lock:
            self._tool_executions.append(record)

        try:
            db = SessionLocal()
            rec = ToolExecutionRecord(
                execution_id=record["execution_id"],
                tool_name=record["tool_name"],
                action_id=record["action_id"],
                payment_id=record["payment_id"],
                status=record["status"],
                policy_token_id=record.get("policy_token_id"),
                parameters_json=record.get("parameters", {}),
                result_json=record.get("result", {}),
            )
            db.add(rec)
            db.commit()
            db.close()
        except Exception:
            pass

    def record_verification(self, record: dict[str, Any]) -> None:
        """Stores verification outcome log in memory and DB."""
        with self._lock:
            self._verifications.append(record)

        try:
            db = SessionLocal()
            rec = VerificationRecord(
                payment_id=record["payment_id"],
                action_id=record["action_id"],
                trace_id=record.get("trace_id"),
                recovery_type=record["recovery_type"],
                is_recovered=record["is_recovered"],
                recovered_amount_minor=record.get("recovered_amount_minor", 0),
            )
            db.add(rec)
            db.commit()
            db.close()
        except Exception:
            pass

    def get_overview_stats(self) -> dict[str, Any]:
        """Calculates aggregate operational metrics across observed entities."""
        with self._lock:
            events = self.ingestion_service.ingested_events
            payment_ids = {e.entity_id for e in events}

            total_payments = len(payment_ids)
            failed_count = 0
            recovered_count = 0
            total_risk_minor = 0
            total_recovered_minor = 0
            total_cost_minor = 0

            for pid in payment_ids:
                p_events = [e for e in events if e.entity_id == pid]
                if not p_events:
                    continue
                payment = self.reconstructor.reconstruct_payment_state(pid, p_events)

                amt = payment.amount.amount_minor if payment.amount else 0
                if payment.status in (PaymentStatus.FAILED, PaymentStatus.AMBIGUOUS):
                    failed_count += 1
                    total_risk_minor += amt
                elif payment.status == PaymentStatus.CAPTURED:
                    recovered_count += 1
                    total_recovered_minor += amt

            traces_list = list(self._traces.values())
            blocked_count = sum(1 for t in traces_list if str(t.status) == "POLICY_BLOCKED")
            escalated_count = sum(1 for t in traces_list if str(t.status) == "ESCALATED")
            approved_count = sum(1 for t in traces_list if str(t.status) in ("POLICY_APPROVED", "EXECUTED", "VERIFIED"))

            rec_rate = (recovered_count / total_payments) if total_payments > 0 else 0.0
            net_recovered = total_recovered_minor - total_cost_minor

            telemetry_logs = self.telemetry.get_logs()
            fallback_count = sum(1 for entry in telemetry_logs if entry.reasoning_mode == "DETERMINISTIC_FALLBACK")
            llm_count = sum(1 for entry in telemetry_logs if entry.reasoning_mode == "LLM")
            latencies = [entry.latency_ms for entry in telemetry_logs]
            avg_latency = (sum(latencies) / len(latencies)) if latencies else 0.0

            return {
                "total_payments": total_payments,
                "failed_payments": failed_count,
                "recovered_payments": recovered_count,
                "recovery_rate": round(rec_rate, 4),
                "total_revenue_at_risk_minor": total_risk_minor,
                "total_revenue_recovered_minor": total_recovered_minor,
                "total_action_cost_minor": total_cost_minor,
                "net_revenue_recovered_minor": net_recovered,
                "blocked_actions": blocked_count,
                "escalations": escalated_count,
                "approved_actions": approved_count,
                "tool_executions": len(self._tool_executions),
                "duplicate_executions_prevented": 0,
                "policy_violations": 0,
                "active_opportunities": failed_count,
                "agent_fallback_count": fallback_count,
                "llm_invocation_count": llm_count,
                "average_agent_latency_ms": round(avg_latency, 2),
                "webhook_count": len(events),
                "duplicate_webhook_count": 0,
            }

    def get_payments(
        self,
        status: str | None = None,
        merchant_id: str | None = None,
        customer_id: str | None = None,
        payment_id: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[dict[str, Any]], int]:
        """Returns paginated payment summary items."""
        events = self.ingestion_service.ingested_events
        payment_ids = sorted(list({e.entity_id for e in events}))

        items: list[dict[str, Any]] = []
        for pid in payment_ids:
            if payment_id and pid != payment_id:
                continue
            p_events = [e for e in events if e.entity_id == pid]
            if not p_events:
                continue
            payment = self.reconstructor.reconstruct_payment_state(pid, p_events)

            if status and payment.status.value.upper() != status.upper():
                continue
            if merchant_id and payment.merchant_id != merchant_id:
                continue
            if customer_id and payment.customer_id != customer_id:
                continue

            last_evt = p_events[-1] if p_events else None
            items.append({
                "payment_id": payment.id,
                "order_id": payment.order_id,
                "merchant_id": payment.merchant_id,
                "customer_id": payment.customer_id,
                "amount_minor": payment.amount.amount_minor if payment.amount else 0,
                "currency": payment.amount.currency if payment.amount else "INR",
                "status": payment.status.value,
                "created_at": payment.created_at,
                "last_event_type": last_evt.event_type if last_evt else None,
                "recovery_status": "CLOSED" if payment.status == PaymentStatus.CAPTURED else "OPEN",
            })

        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return items[start:end], total

    def get_payment_detail(self, payment_id: str) -> dict[str, Any] | None:
        """Returns detailed payment object including reconstructed state and trace reference."""
        events = self.ingestion_service.get_events_for_entity(payment_id)
        if not events:
            return None

        payment = self.reconstructor.reconstruct_payment_state(payment_id, events)
        traces = [t for t in self._traces.values() if t.payment_id == payment_id]
        latest_trace = traces[-1] if traces else None

        last_evt = events[-1] if events else None
        err_code = last_evt.payload.get("error_code") if last_evt and last_evt.payload else None
        err_desc = last_evt.payload.get("error_description") if last_evt and last_evt.payload else None

        return {
            "payment_id": payment.id,
            "order_id": payment.order_id,
            "merchant_id": payment.merchant_id,
            "customer_id": payment.customer_id,
            "amount_minor": payment.amount.amount_minor if payment.amount else 0,
            "currency": payment.amount.currency if payment.amount else "INR",
            "status": payment.status.value,
            "attempts_count": len(payment.attempts),
            "error_code": err_code,
            "error_description": err_desc,
            "events": [e.model_dump() for e in events],
            "candidate_actions": latest_trace.candidate_actions if latest_trace else [],
            "policy_decision": latest_trace.policy_evaluations[-1] if (latest_trace and latest_trace.policy_evaluations) else None,
            "execution_result": latest_trace.execution_result if latest_trace else None,
            "verification_result": latest_trace.verification_result if latest_trace else None,
            "latest_trace_id": latest_trace.decision_id if latest_trace else None,
        }

    def get_events(
        self,
        entity_id: str | None = None,
        event_id: str | None = None,
        event_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[FinancialEvent], int]:
        """Returns paginated FinancialEvent list."""
        events = self.ingestion_service.ingested_events
        filtered: list[FinancialEvent] = []

        for e in events:
            if entity_id and e.entity_id != entity_id:
                continue
            if event_id and e.id != event_id:
                continue
            if event_type and e.event_type.lower() != event_type.lower():
                continue
            filtered.append(e)

        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        return filtered[start:end], total

    def get_traces(
        self,
        trace_id: str | None = None,
        payment_id: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[DecisionTrace], int]:
        """Returns paginated DecisionTrace list."""
        traces = list(self._traces.values())
        filtered: list[DecisionTrace] = []

        for t in traces:
            if trace_id and t.decision_id != trace_id:
                continue
            if payment_id and t.payment_id != payment_id:
                continue
            if status and str(t.status).upper() != status.upper():
                continue
            filtered.append(t)

        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        return filtered[start:end], total

    def get_policies(self) -> list[dict[str, Any]]:
        """Returns registered PolicyEngine rule metadata summaries."""
        registered = get_registered_policies()
        policies_metadata = []

        for pol_id, pol_obj in registered.items():
            policies_metadata.append({
                "policy_id": pol_id,
                "name": pol_obj.name,
                "description": pol_obj.description,
                "decision_type": pol_obj.decision_type,
                "version": "v1.0",
                "evaluations_count": 1,
                "triggers_count": 0,
            })

        return policies_metadata

    def get_tool_executions(
        self,
        payment_id: str | None = None,
        tool_name: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[dict[str, Any]], int]:
        """Returns paginated tool execution logs."""
        filtered: list[dict[str, Any]] = []

        for rec in self._tool_executions:
            if payment_id and rec.get("payment_id") != payment_id:
                continue
            if tool_name and rec.get("tool_name") != tool_name:
                continue
            if status and rec.get("status") != status:
                continue
            filtered.append(rec)

        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        return filtered[start:end], total

    def get_verifications(
        self,
        payment_id: str | None = None,
        recovery_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[dict[str, Any]], int]:
        """Returns paginated verification logs."""
        filtered: list[dict[str, Any]] = []

        for rec in self._verifications:
            if payment_id and rec.get("payment_id") != payment_id:
                continue
            if recovery_type and rec.get("recovery_type") != recovery_type:
                continue
            filtered.append(rec)

        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        return filtered[start:end], total

    def get_benchmark_report(self) -> BenchmarkReport:
        """Reads persisted benchmark JSON report if available, else builds default."""
        json_path = os.path.abspath("data/evaluation/benchmark_results_v1.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return BenchmarkReport.model_validate(data)

        from ml.evaluation.runner import BenchmarkRunner
        return BenchmarkRunner(seed=42).run_benchmark()
