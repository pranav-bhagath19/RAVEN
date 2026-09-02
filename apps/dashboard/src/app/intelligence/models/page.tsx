"use client";

import React from "react";
import Link from "next/link";
import { StatusBadge } from "../../../components/StatusBadge";
import { ArrowLeft, Layers, Lock, ShieldCheck } from "lucide-react";

export default function ModelsPage() {
  const models = [
    { name: "linucb_propensity_v2", version: "v2.4.0", type: "LinUCB Contextual Bandit", status: "CHAMPION", accuracy: "89.2%", trained: "2026-08-30" },
    { name: "logistic_propensity_v1", version: "v1.8.0", type: "Logistic Regression", status: "CHALLENGER", accuracy: "84.5%", trained: "2026-08-28" },
    { name: "baseline_heuristic_v1", version: "v1.0.0", type: "Rule Baseline", status: "SUPERSEDED", accuracy: "71.0%", trained: "2026-08-15" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Link
            href="/intelligence"
            className="p-1.5 bg-white border border-slate-200 rounded-lg text-slate-600 hover:text-slate-900 shadow-2xs"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center">
              <Layers className="w-5 h-5 text-blue-600 mr-2" /> Model Registry & Promotion History
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">Machine Learning model inventory and champion/challenger states</p>
          </div>
        </div>
      </div>

      {/* Security Rule Notice */}
      <div className="bg-slate-100 border border-slate-300 text-slate-800 rounded-xl p-4 flex items-center space-x-3">
        <Lock className="w-4 h-4 text-slate-600 shrink-0" />
        <p className="text-xs font-medium">
          Model promotion is backend-authorized only. The frontend dashboard does not allow unauthorized model promotion.
        </p>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[11px]">
              <th className="p-3.5">Model Name</th>
              <th className="p-3.5">Version</th>
              <th className="p-3.5">Architecture</th>
              <th className="p-3.5">Accuracy</th>
              <th className="p-3.5">Trained Date</th>
              <th className="p-3.5 text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {models.map((m) => (
              <tr key={m.version} className="hover:bg-slate-50/80 transition-colors">
                <td className="p-3.5 font-mono font-bold text-slate-900">{m.name}</td>
                <td className="p-3.5 font-mono text-blue-600">{m.version}</td>
                <td className="p-3.5 font-semibold text-slate-700">{m.type}</td>
                <td className="p-3.5 font-mono font-bold text-emerald-600">{m.accuracy}</td>
                <td className="p-3.5 text-slate-500 font-mono">{m.trained}</td>
                <td className="p-3.5 text-right">
                  <StatusBadge status={m.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
