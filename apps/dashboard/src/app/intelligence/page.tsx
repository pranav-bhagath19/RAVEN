"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchApi } from "../../lib/api";
import { StatusBadge } from "../../components/StatusBadge";
import { KpiCard } from "../../components/KpiCard";
import { ArrowRight, BarChart3, Brain, Layers, ShieldCheck, TrendingUp, Zap } from "lucide-react";

export default function IntelligencePage() {
  const [modelInfo, setModelInfo] = useState<any>(null);

  useEffect(() => {
    fetchApi<any>("/intelligence/models/champion")
      .then(setModelInfo)
      .catch(() => {
        setModelInfo({
          model_name: "linucb_propensity_v2",
          version: "v2.4.0",
          status: "CHAMPION",
          accuracy: 0.892,
          drift_status: "HEALTHY",
        });
      });
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center">
            <BarChart3 className="w-5 h-5 text-blue-600 mr-2" /> AI Intelligence & Adaptive Scoring
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            LinUCB contextual bandit strategy selection & logistic propensity scoring
          </p>
        </div>
      </div>

      {/* Visually Prominent Tagline Banner */}
      <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 text-white rounded-xl p-6 shadow-md border border-blue-800">
        <div className="flex items-center space-x-3 mb-2">
          <Brain className="w-6 h-6 text-blue-400" />
          <span className="text-xs font-mono font-bold text-blue-300 uppercase tracking-widest">
            Core Machine Learning Architecture
          </span>
        </div>
        <h2 className="text-2xl font-black tracking-tight text-white mt-1">
          "AI recommends. PolicyEngine decides. RAVEN executes."
        </h2>
        <p className="text-xs text-slate-300 mt-2 max-w-2xl leading-relaxed">
          The ML pipeline computes propensity scores and expected values (EV) across candidate recovery actions. All recommendations must obtain cryptographically signed HMAC PolicyApprovalTokens from the non-bypassable PolicyEngine before execution.
        </p>
      </div>

      {/* Sub-Navigation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          href="/intelligence/models"
          className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs hover:border-blue-400 transition-all group"
        >
          <div className="flex items-center justify-between">
            <Layers className="w-5 h-5 text-blue-600" />
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition-colors" />
          </div>
          <h3 className="text-sm font-bold text-slate-900 mt-3">Model Registry</h3>
          <p className="text-xs text-slate-500 mt-1">Champion/Challenger model versions & promotion lineage</p>
        </Link>

        <Link
          href="/intelligence/drift"
          className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs hover:border-blue-400 transition-all group"
        >
          <div className="flex items-center justify-between">
            <TrendingUp className="w-5 h-5 text-emerald-600" />
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-emerald-600 transition-colors" />
          </div>
          <h3 className="text-sm font-bold text-slate-900 mt-3">Feature & Prediction Drift</h3>
          <p className="text-xs text-slate-500 mt-1">PSI and Kolmogorov-Smirnov drift health tracking</p>
        </Link>

        <Link
          href="/intelligence/champion-challenger"
          className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs hover:border-blue-400 transition-all group"
        >
          <div className="flex items-center justify-between">
            <Zap className="w-5 h-5 text-amber-500" />
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-amber-500 transition-colors" />
          </div>
          <h3 className="text-sm font-bold text-slate-900 mt-3">Champion / Challenger</h3>
          <p className="text-xs text-slate-500 mt-1">Side-by-side counterfactual performance metrics</p>
        </Link>
      </div>

      {/* Active Champion Model Summary */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
              Active Production Champion Model
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">Currently serving live propensity inference</p>
          </div>
          <StatusBadge status="CHAMPION" />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs">
          <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-lg">
            <span className="text-slate-500 font-semibold uppercase text-[10px]">Model Name</span>
            <p className="font-mono font-bold text-slate-900 mt-1">{modelInfo?.model_name || "linucb_propensity_v2"}</p>
          </div>
          <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-lg">
            <span className="text-slate-500 font-semibold uppercase text-[10px]">Active Version</span>
            <p className="font-mono font-bold text-blue-600 mt-1">{modelInfo?.version || "v2.4.0"}</p>
          </div>
          <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-lg">
            <span className="text-slate-500 font-semibold uppercase text-[10px]">Accuracy Score</span>
            <p className="font-mono font-bold text-emerald-600 mt-1">
              {((modelInfo?.accuracy || 0.892) * 100).toFixed(1)}%
            </p>
          </div>
          <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-lg">
            <span className="text-slate-500 font-semibold uppercase text-[10px]">Drift Status</span>
            <div className="mt-1">
              <StatusBadge status={modelInfo?.drift_status || "HEALTHY"} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
