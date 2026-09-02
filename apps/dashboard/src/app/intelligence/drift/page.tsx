"use client";

import React from "react";
import Link from "next/link";
import { StatusBadge } from "../../../components/StatusBadge";
import { ArrowLeft, TrendingUp, CheckCircle2, AlertTriangle } from "lucide-react";

export default function DriftPage() {
  const driftFeatures = [
    { feature: "amount_minor", psi: 0.021, status: "HEALTHY", ks_stat: 0.015, p_value: 0.84 },
    { feature: "time_since_failure_sec", psi: 0.045, status: "HEALTHY", ks_stat: 0.022, p_value: 0.62 },
    { feature: "customer_historical_success_rate", psi: 0.089, status: "HEALTHY", ks_stat: 0.041, p_value: 0.35 },
    { feature: "issuer_bank_latency_ms", psi: 0.142, status: "WARNING", ks_stat: 0.085, p_value: 0.08 },
    { feature: "device_channel_category", psi: 0.012, status: "HEALTHY", ks_stat: 0.009, p_value: 0.95 },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-3">
        <Link
          href="/intelligence"
          className="p-1.5 bg-white border border-slate-200 rounded-lg text-slate-600 hover:text-slate-900 shadow-2xs"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center">
            <TrendingUp className="w-5 h-5 text-emerald-600 mr-2" /> Feature & Prediction Drift Health
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Population Stability Index (PSI) and Kolmogorov-Smirnov statistical feature drift tracking
          </p>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[11px]">
              <th className="p-3.5">Feature Name</th>
              <th className="p-3.5">PSI Metric</th>
              <th className="p-3.5">KS Statistic</th>
              <th className="p-3.5">P-Value</th>
              <th className="p-3.5 text-right">Drift Health Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {driftFeatures.map((f) => (
              <tr key={f.feature} className="hover:bg-slate-50/80 transition-colors">
                <td className="p-3.5 font-mono font-bold text-slate-900">{f.feature}</td>
                <td className="p-3.5 font-mono font-semibold text-slate-800">{f.psi}</td>
                <td className="p-3.5 font-mono text-slate-700">{f.ks_stat}</td>
                <td className="p-3.5 font-mono text-slate-700">{f.p_value}</td>
                <td className="p-3.5 text-right">
                  <StatusBadge status={f.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
