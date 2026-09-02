"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchApi } from "../../lib/api";
import { KpiCard } from "../../components/KpiCard";
import { StatusBadge } from "../../components/StatusBadge";
import { TableSkeleton } from "../../components/SkeletonLoader";
import {
  Activity,
  AlertCircle,
  ArrowRight,
  BarChart3,
  Brain,
  CheckCircle2,
  Clock,
  CreditCard,
  DollarSign,
  ExternalLink,
  GitCommit,
  Layers,
  RefreshCw,
  ShieldCheck,
  TrendingUp,
  Zap,
} from "lucide-react";

interface OverviewData {
  revenue_at_risk_minor: number;
  revenue_recovered_minor: number;
  recovery_rate_pct: number;
  revenue_recovery_value_rate_pct: number;
  failed_payments: number;
  actions_attempted: number;
  successful_recoveries: number;
  policy_veto_count: number;
  duplicate_execution_count: number;
  average_decision_latency_seconds: number;
}

export default function DashboardPage() {
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [payments, setPayments] = useState<any[]>([]);
  const [decisions, setDecisions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState("30D");

  useEffect(() => {
    Promise.all([
      fetchApi<OverviewData>("/operations/overview").catch(() => null),
      fetchApi<any>("/operations/payments").catch(() => null),
      fetchApi<any>("/operations/decisions").catch(() => null),
    ]).then(([overviewRes, paymentsRes, decisionsRes]) => {
      if (overviewRes) {
        setOverview(overviewRes);
      } else {
        setOverview({
          revenue_at_risk_minor: 0,
          revenue_recovered_minor: 0,
          recovery_rate_pct: 0,
          revenue_recovery_value_rate_pct: 0,
          failed_payments: 0,
          actions_attempted: 0,
          successful_recoveries: 0,
          policy_veto_count: 0,
          duplicate_execution_count: 0,
          average_decision_latency_seconds: 0,
        });
      }

      const paymentList = Array.isArray(paymentsRes)
        ? paymentsRes
        : paymentsRes?.items || [];
      setPayments(paymentList.slice(0, 5));

      const decisionList = Array.isArray(decisionsRes)
        ? decisionsRes
        : decisionsRes?.items || [];
      setDecisions(decisionList.slice(0, 5));

      setLoading(false);
    });
  }, []);

  const formatINR = (minorUnits: number) => {
    return `₹${(minorUnits / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
  };

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-2xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="bg-blue-50 text-[#0570DE] border border-blue-200 text-[11px] font-bold px-2.5 py-0.5 rounded-md uppercase tracking-wider font-sans">
                Razorpay AI Buildathon Track 03
              </span>
              <span className="text-xs text-slate-500 font-semibold">Live Operations Control Plane</span>
            </div>
            <h1 className="text-2xl font-black text-slate-900 tracking-tight mt-2 font-sans">Revenue Recovery Overview</h1>
            <p className="text-xs text-slate-500 font-medium mt-1 max-w-3xl leading-relaxed">
              Autonomous payment recovery powered by deterministic State Reconstruction, LinUCB adaptive intelligence, and non-bypassable PolicyEngine veto boundaries.
            </p>
          </div>

          <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-lg border border-slate-200/80 shrink-0">
            {["Today", "7D", "30D", "Custom"].map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${
                  period === p
                    ? "bg-white text-[#0570DE] shadow-2xs border border-slate-200/60"
                    : "text-slate-600 hover:text-slate-900 font-semibold"
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* AI vs Policy Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-600 text-white rounded-lg">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Safety Architecture Principle
            </h4>
            <p className="text-xs font-semibold text-blue-900 mt-0.5">
              "AI recommends. PolicyEngine decides. RAVEN executes."
            </p>
          </div>
        </div>
        <Link
          href="/policies"
          className="text-xs font-bold text-blue-600 hover:text-blue-800 flex items-center space-x-1"
        >
          <span>Inspect POL_001–POL_007</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <KpiCard
          title="Revenue at Risk"
          value={overview ? formatINR(overview.revenue_at_risk_minor) : "₹0.00"}
          subtext="Total failed payment volume"
          icon={AlertCircle}
          accentColor="rose"
          loading={loading}
        />
        <KpiCard
          title="Revenue Recovered"
          value={overview ? formatINR(overview.revenue_recovered_minor) : "₹0.00"}
          subtext="Ground-truth captured revenue"
          icon={CheckCircle2}
          accentColor="emerald"
          loading={loading}
        />
        <KpiCard
          title="Recovery Value Rate"
          value={overview ? `${overview.revenue_recovery_value_rate_pct}%` : "0%"}
          subtext="Percent of minor unit value recovered"
          icon={TrendingUp}
          accentColor="blue"
          loading={loading}
        />
        <KpiCard
          title="Failed Payments Ingested"
          value={overview ? overview.failed_payments : 0}
          subtext="Razorpay failure webhooks"
          icon={CreditCard}
          accentColor="amber"
          loading={loading}
        />
        <KpiCard
          title="Recovery Attempts"
          value={overview ? overview.actions_attempted : 0}
          subtext="Bounded tool executions"
          icon={Zap}
          accentColor="indigo"
          loading={loading}
        />
        <KpiCard
          title="Policy Vetoes Enforced"
          value={overview ? overview.policy_veto_count : 0}
          subtext="Non-bypassable safety vetoes"
          icon={ShieldCheck}
          accentColor="rose"
          loading={loading}
        />
      </div>

      {/* Recent Activity Dual Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Ingested Payments */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center">
              <CreditCard className="w-4 h-4 text-blue-600 mr-2" /> Live Failed Payments
            </h3>
            <Link href="/payments" className="text-xs font-semibold text-blue-600 hover:text-blue-800">
              View Directory
            </Link>
          </div>

          <div className="space-y-3">
            {payments.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-400 font-medium">
                No failed payments recorded yet.
              </div>
            ) : (
              payments.map((item) => (
                <div key={item.payment_id} className="p-3 bg-slate-50 border border-slate-200/80 rounded-lg flex items-center justify-between">
                  <div>
                    <span className="font-mono text-xs font-bold text-slate-800">{item.payment_id}</span>
                    <span className="block text-[11px] font-semibold text-slate-500 mt-0.5">
                      {item.error_code || "BAD_REQUEST_PAYMENT_DECLINED"}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="font-mono text-xs font-bold text-slate-900">{formatINR(item.amount_minor || 0)}</span>
                    <div className="mt-1">
                      <StatusBadge status={item.status} />
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Decision Traces */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center">
              <GitCommit className="w-4 h-4 text-indigo-600 mr-2" /> Recent Decision Traces
            </h3>
            <Link href="/decisions" className="text-xs font-semibold text-blue-600 hover:text-blue-800">
              View Audit Log
            </Link>
          </div>

          <div className="space-y-3">
            {decisions.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-400 font-medium">
                No decision traces recorded yet.
              </div>
            ) : (
              decisions.map((item) => (
                <div key={item.decision_id || item.trace_id} className="p-3 bg-slate-50 border border-slate-200/80 rounded-lg flex items-center justify-between">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs font-bold text-slate-900">{item.decision_id || item.trace_id}</span>
                      <span className="text-[10px] text-slate-400 font-mono">({item.payment_id})</span>
                    </div>
                    <span className="block text-[11px] font-semibold text-slate-600 mt-0.5">{item.selected_action_type || item.recommended_action}</span>
                  </div>
                  <div className="text-right">
                    <StatusBadge status={item.policy_decision || item.status} />
                    <span className="block text-[10px] font-mono text-slate-400 mt-1">{item.policy_token_id || "POL_VETO"}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
