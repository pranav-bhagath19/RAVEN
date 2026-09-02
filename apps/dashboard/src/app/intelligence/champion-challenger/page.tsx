"use client";

import React from "react";
import Link from "next/link";
import { StatusBadge } from "../../../components/StatusBadge";
import { ArrowLeft, CheckCircle2, Layers, ShieldCheck, Zap } from "lucide-react";

export default function ChampionChallengerPage() {
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
            <Zap className="w-5 h-5 text-amber-500 mr-2" /> Champion / Challenger Comparison
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Side-by-side counterfactual performance metrics for production model evaluation
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Champion Model Card */}
        <div className="bg-white border-2 border-blue-500 rounded-xl p-6 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
            <div>
              <span className="text-[10px] font-mono font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                CURRENT CHAMPION (ACTIVE)
              </span>
              <h3 className="text-lg font-extrabold text-slate-900 mt-1">linucb_propensity_v2</h3>
            </div>
            <StatusBadge status="CHAMPION" />
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-1.5 border-b border-slate-50">
              <span className="text-slate-500 font-medium">Architecture</span>
              <span className="font-semibold text-slate-800">LinUCB Contextual Bandit</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-50">
              <span className="text-slate-500 font-medium">Recovery Accuracy</span>
              <span className="font-mono font-bold text-emerald-600">89.2%</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-50">
              <span className="text-slate-500 font-medium">Value Recovery Rate</span>
              <span className="font-mono font-bold text-blue-600">50.79%</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-50">
              <span className="text-slate-500 font-medium">Policy Veto Rate</span>
              <span className="font-mono font-bold text-slate-700">30.0%</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-500 font-medium">Average Latency</span>
              <span className="font-mono font-bold text-slate-800">1.2 ms</span>
            </div>
          </div>
        </div>

        {/* Challenger Model Card */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs relative overflow-hidden">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
            <div>
              <span className="text-[10px] font-mono font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                CHALLENGER (SHADOW EVALUATION)
              </span>
              <h3 className="text-lg font-extrabold text-slate-900 mt-1">logistic_propensity_v1</h3>
            </div>
            <StatusBadge status="CHALLENGER" />
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-1.5 border-b border-slate-50">
              <span className="text-slate-500 font-medium">Architecture</span>
              <span className="font-semibold text-slate-800">Logistic Regression</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-50">
              <span className="text-slate-500 font-medium">Recovery Accuracy</span>
              <span className="font-mono font-bold text-slate-700">84.5%</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-50">
              <span className="text-slate-500 font-medium">Value Recovery Rate</span>
              <span className="font-mono font-bold text-slate-700">44.20%</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-50">
              <span className="text-slate-500 font-medium">Policy Veto Rate</span>
              <span className="font-mono font-bold text-slate-700">36.5%</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-500 font-medium">Average Latency</span>
              <span className="font-mono font-bold text-slate-800">0.8 ms</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
