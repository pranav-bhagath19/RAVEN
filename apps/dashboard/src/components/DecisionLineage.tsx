"use client";

import React from "react";
import { AlertCircle, ArrowRight, Brain, CheckCircle2, ShieldCheck, Key, Zap, Lock } from "lucide-react";

interface DecisionLineageProps {
  paymentId?: string;
  rootCause?: string;
  actionType?: string;
  propensityScore?: number;
  expectedValueINR?: number;
  policyDecision?: string;
  tokenVerified?: boolean;
  executionStatus?: string;
  verificationStatus?: string;
}

export function DecisionLineage({
  paymentId = "",
  rootCause = "INSUFFICIENT_FUNDS",
  actionType = "PAYMENT_LINK",
  propensityScore = 0.84,
  expectedValueINR = 1499.0,
  policyDecision = "APPROVED",
  tokenVerified = true,
  executionStatus = "SUCCESS",
  verificationStatus = "CAPTURED",
}: DecisionLineageProps) {
  const steps = [
    {
      title: "1. Payment Failure Ingested",
      desc: paymentId,
      icon: AlertCircle,
      badge: "INGESTED",
      color: "bg-amber-50 text-amber-700 border-amber-200",
    },
    {
      title: "2. Root Cause Analysis",
      desc: rootCause,
      icon: Brain,
      badge: "DIAGNOSED",
      color: "bg-blue-50 text-blue-700 border-blue-200",
    },
    {
      title: "3. ML Propensity & EV",
      desc: `Score: ${(propensityScore * 100).toFixed(0)}% | EV: ₹${expectedValueINR.toFixed(2)}`,
      icon: Zap,
      badge: actionType,
      color: "bg-indigo-50 text-indigo-700 border-indigo-200",
    },
    {
      title: "4. PolicyEngine Check",
      desc: policyDecision === "APPROVED" ? "POL_001–POL_007 Satisfied" : "Policy Veto Enforced",
      icon: ShieldCheck,
      badge: policyDecision,
      color: policyDecision === "APPROVED" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-rose-50 text-rose-700 border-rose-200",
    },
    {
      title: "5. HMAC Approval Token",
      desc: tokenVerified ? "HMAC-SHA256 Signed" : "Token Invalid",
      icon: Key,
      badge: tokenVerified ? "VERIFIED" : "UNVERIFIED",
      color: tokenVerified ? "bg-purple-50 text-purple-700 border-purple-200" : "bg-rose-50 text-rose-700 border-rose-200",
    },
    {
      title: "6. Tool Execution Boundary",
      desc: executionStatus === "SUCCESS" ? "Bounded Action Executed" : "Execution Blocked",
      icon: Lock,
      badge: executionStatus,
      color: executionStatus === "SUCCESS" ? "bg-sky-50 text-sky-700 border-sky-200" : "bg-rose-50 text-rose-700 border-rose-200",
    },
    {
      title: "7. Ground-Truth Verified",
      desc: `Status: ${verificationStatus}`,
      icon: CheckCircle2,
      badge: "ATTRIBUTED",
      color: "bg-emerald-50 text-emerald-700 border-emerald-200",
    },
  ];

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-6">
        <div>
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center">
            <Brain className="w-4 h-4 text-blue-600 mr-2" /> Autonomous Decision Lineage Flow
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            AI recommends. PolicyEngine decides. ToolExecutor executes.
          </p>
        </div>
        <span className="text-[11px] font-mono font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-md border border-slate-200">
          Trace: {paymentId}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-7 gap-3 relative">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          return (
            <React.Fragment key={idx}>
              <div className="bg-slate-50/70 border border-slate-200/80 rounded-lg p-3 flex flex-col justify-between hover:border-slate-300 transition-all">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Icon className="w-4 h-4 text-slate-700" />
                    <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${step.color}`}>
                      {step.badge}
                    </span>
                  </div>
                  <h4 className="text-[11px] font-bold text-slate-800 leading-tight">{step.title}</h4>
                  <p className="text-[10px] text-slate-500 mt-1 font-mono break-all">{step.desc}</p>
                </div>
              </div>
              {idx < steps.length - 1 && (
                <div className="hidden md:flex items-center justify-center -mx-2 text-slate-300">
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
