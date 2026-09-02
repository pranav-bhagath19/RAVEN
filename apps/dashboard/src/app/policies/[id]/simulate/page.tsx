"use client";

import React, { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { StatusBadge } from "../../../../components/StatusBadge";
import { ArrowLeft, Play, ShieldAlert, ShieldCheck, Zap } from "lucide-react";

export default function PolicySimulatePage() {
  const params = useParams();
  const policyId = (params?.id as string) || "POL_001";

  const [amount, setAmount] = useState("1499.00");
  const [errorCode, setErrorCode] = useState("INSUFFICIENT_FUNDS");
  const [candidateAction, setCandidateAction] = useState("PAYMENT_LINK");
  const [simulated, setSimulated] = useState<any | null>(null);

  const handleSimulate = (e: React.FormEvent) => {
    e.preventDefault();
    const amtMinor = Math.round(parseFloat(amount) * 100);
    const veto = amtMinor > 5000000 && candidateAction === "SMART_RETRY";

    setSimulated({
      isSimulation: true,
      policy_id: policyId,
      decision: veto ? "VETOED" : "APPROVED",
      veto_reason: veto ? "POL_002: High-value transaction threshold exceeded" : null,
      expected_value_inr: veto ? 0 : parseFloat(amount) * 0.84,
      propensity_score: 0.84,
      approval_token_mock: veto ? "VETO_ENFORCED" : "sim_tok_hmac_991823",
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Link
            href={`/policies/${policyId}`}
            className="p-1.5 bg-white border border-slate-200 rounded-lg text-slate-600 hover:text-slate-900 shadow-2xs"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                Policy Counterfactual Simulator
              </h1>
              <StatusBadge status="SIMULATION" />
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Simulate PolicyEngine veto evaluation and Expected Value (EV) without side-effects
            </p>
          </div>
        </div>
      </div>

      {/* Prominent Counterfactual Banner */}
      <div className="bg-amber-50 border border-amber-200 text-amber-900 rounded-xl p-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0" />
          <p className="text-xs font-semibold">
            NOTICE: Results generated in this tool are strictly <strong>COUNTERFACTUAL / SIMULATION</strong> outputs. No real financial tools or notification channels are triggered.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Input Parameters Form */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-3 mb-4">
            Simulation Inputs
          </h3>

          <form onSubmit={handleSimulate} className="space-y-4 text-xs">
            <div>
              <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">
                Transaction Amount (INR)
              </label>
              <input
                type="number"
                step="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 font-mono font-bold focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">
                Failure Error Code
              </label>
              <select
                value={errorCode}
                onChange={(e) => setErrorCode(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 font-semibold focus:ring-2 focus:ring-blue-500 focus:outline-none"
              >
                <option value="INSUFFICIENT_FUNDS">INSUFFICIENT_FUNDS</option>
                <option value="BAD_REQUEST_PAYMENT_DECLINED">BAD_REQUEST_PAYMENT_DECLINED</option>
                <option value="GATEWAY_TIMEOUT">GATEWAY_TIMEOUT</option>
              </select>
            </div>

            <div>
              <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">
                Candidate Recovery Action
              </label>
              <select
                value={candidateAction}
                onChange={(e) => setCandidateAction(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-slate-900 font-semibold focus:ring-2 focus:ring-blue-500 focus:outline-none"
              >
                <option value="PAYMENT_LINK">PAYMENT_LINK (Razorpay Link)</option>
                <option value="SMART_RETRY">SMART_RETRY (Gateway Retry)</option>
                <option value="FALLBACK_NOTIFY">FALLBACK_NOTIFY (Customer Alert)</option>
              </select>
            </div>

            <button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg shadow-xs transition-colors flex items-center justify-center space-x-2 mt-4"
            >
              <Play className="w-4 h-4" />
              <span>Run Counterfactual Simulation</span>
            </button>
          </form>
        </div>

        {/* Counterfactual Results Output */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
              <h3 className="text-sm font-bold text-slate-900">Simulation Output</h3>
              <StatusBadge status="COUNTERFACTUAL" />
            </div>

            {simulated ? (
              <div className="space-y-3 text-xs">
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between">
                  <span className="text-slate-600 font-medium">Policy Engine Evaluation</span>
                  <StatusBadge status={simulated.decision} />
                </div>

                {simulated.veto_reason && (
                  <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg font-mono text-[11px]">
                    {simulated.veto_reason}
                  </div>
                )}

                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between">
                  <span className="text-slate-600 font-medium">Simulated Expected Value (EV)</span>
                  <span className="font-mono font-bold text-emerald-600 text-sm">
                    ₹{simulated.expected_value_inr.toFixed(2)}
                  </span>
                </div>

                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between">
                  <span className="text-slate-600 font-medium">Propensity Score</span>
                  <span className="font-mono font-bold text-blue-600">
                    {(simulated.propensity_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-slate-400 font-medium">
                Configure inputs and click "Run Counterfactual Simulation".
              </div>
            )}
          </div>

          <div className="mt-6 pt-3 border-t border-slate-100 text-[11px] text-slate-400 font-mono">
            Label: COUNTERFACTUAL / SIMULATION (No DB mutations performed)
          </div>
        </div>
      </div>
    </div>
  );
}
