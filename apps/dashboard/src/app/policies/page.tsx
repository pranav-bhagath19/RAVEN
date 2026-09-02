"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchApi } from "../../lib/api";
import { StatusBadge } from "../../components/StatusBadge";
import { TableSkeleton } from "../../components/SkeletonLoader";
import { ArrowRight, CheckCircle2, Play, ShieldAlert, ShieldCheck, Sliders } from "lucide-react";

export default function PoliciesPage() {
  const [policies, setPolicies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApi<any[]>("/policies")
      .then((data) => {
        setPolicies(data);
        setLoading(false);
      })
      .catch(() => {
        setPolicies([
          { policy_id: "POL_001", name: "Max Retry Rate Cap", status: "ACTIVE", max_retries: 3, active_version: "v1.2.0" },
          { policy_id: "POL_002", name: "High-Value Transaction Threshold", status: "ACTIVE", threshold_minor: 5000000, active_version: "v1.0.0" },
          { policy_id: "POL_003", name: "Minimum Propensity EV Floor", status: "ACTIVE", min_propensity: 0.35, active_version: "v2.1.0" },
          { policy_id: "POL_004", name: "Customer Notification Fatigue Limit", status: "ACTIVE", max_notifications_24h: 2, active_version: "v1.0.0" },
          { policy_id: "POL_005", name: "Circuit Breaker Fail-Closed Protection", status: "ACTIVE", max_consecutive_failures: 5, active_version: "v1.0.0" },
          { policy_id: "POL_006", name: "HMAC Ephemeral Token Expiration", status: "ACTIVE", token_ttl_seconds: 300, active_version: "v1.1.0" },
          { policy_id: "POL_007", name: "Deterministic Verification Required", status: "ACTIVE", enforce_capture_verification: true, active_version: "v1.0.0" },
        ]);
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center">
            <ShieldCheck className="w-5 h-5 text-emerald-600 mr-2" /> PolicyEngine Safety Console
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Non-bypassable safety rules POL_001 through POL_007 governing autonomous recovery actions
          </p>
        </div>
      </div>

      {/* Safety Motto Banner */}
      <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-emerald-600 text-white rounded-lg">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Enforcement Invariant
            </h4>
            <p className="text-xs font-semibold text-emerald-900 mt-0.5">
              PolicyEngine veto authority cannot be bypassed by ML models or LLM recommendations.
            </p>
          </div>
        </div>
      </div>

      {loading ? (
        <TableSkeleton rows={5} cols={5} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {policies.map((p) => (
            <div key={p.policy_id} className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs hover:border-slate-300 transition-all flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
                    {p.policy_id}
                  </span>
                  <StatusBadge status={p.status || "ACTIVE"} />
                </div>
                <h3 className="text-sm font-bold text-slate-900 mt-1">{p.name}</h3>
                <p className="text-xs text-slate-500 mt-1">
                  Active Version: <code className="font-mono font-semibold text-slate-700">{p.active_version || "v1.0.0"}</code>
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                <Link
                  href={`/policies/${p.policy_id}/simulate`}
                  className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center"
                >
                  <Play className="w-3 h-3 mr-1" /> Counterfactual Simulator
                </Link>
                <Link
                  href={`/policies/${p.policy_id}`}
                  className="text-xs font-bold text-slate-700 hover:text-slate-900 flex items-center"
                >
                  <span>Details</span>
                  <ArrowRight className="w-3.5 h-3.5 ml-1" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
