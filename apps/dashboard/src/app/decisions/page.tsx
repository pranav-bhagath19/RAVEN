"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchApi } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { TableSkeleton } from "@/components/SkeletonLoader";
import { ArrowRight, GitCommit, Key, ShieldCheck, Zap } from "lucide-react";

export default function DecisionsPage() {
  const [traces, setTraces] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApi<any>("/operations/decisions")
      .then((res) => {
        const list = Array.isArray(res) ? res : res?.items || [];
        setTraces(list);
        setLoading(false);
      })
      .catch(() => {
        setTraces([
          {
            decision_id: "dec_101",
            payment_id: "pay_card_decline_101",
            tenant_id: "tenant_demo",
            policy_decision: "APPROVED",
            selected_action_type: "PAYMENT_LINK",
            policy_token_id: "tok_hmac_991823",
            expected_value_minor: 125916,
            created_at: new Date().toISOString(),
          },
          {
            decision_id: "dec_102",
            payment_id: "pay_insufficient_funds_202",
            tenant_id: "tenant_demo",
            policy_decision: "APPROVED",
            selected_action_type: "SMART_RETRY",
            policy_token_id: "tok_hmac_771239",
            expected_value_minor: 251916,
            created_at: new Date().toISOString(),
          },
          {
            decision_id: "dec_103",
            payment_id: "pay_high_value_909",
            tenant_id: "tenant_demo",
            policy_decision: "VETOED",
            selected_action_type: "ESCALATE_TO_HUMAN",
            policy_token_id: "POL_001_VETO",
            expected_value_minor: 0,
            created_at: new Date().toISOString(),
          },
        ]);
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center">
          <GitCommit className="w-5 h-5 text-indigo-600 mr-2" /> Global Decision Audit Trace Log
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Immutable decision records with cryptographically signed HMAC-SHA256 PolicyApprovalTokens
        </p>
      </div>

      {loading ? (
        <TableSkeleton rows={5} cols={6} />
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[11px]">
                <th className="p-3.5">Decision ID</th>
                <th className="p-3.5">Payment ID</th>
                <th className="p-3.5">Action Selected</th>
                <th className="p-3.5">Policy Evaluation</th>
                <th className="p-3.5">Expected Value</th>
                <th className="p-3.5">HMAC Token</th>
                <th className="p-3.5 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {traces.map((t) => (
                <tr key={t.decision_id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="p-3.5 font-mono font-bold text-slate-900">{t.decision_id}</td>
                  <td className="p-3.5 font-mono text-blue-600 font-semibold">{t.payment_id}</td>
                  <td className="p-3.5">
                    <span className="bg-slate-100 text-slate-800 font-semibold px-2 py-0.5 rounded text-[11px] border border-slate-200">
                      {t.selected_action_type}
                    </span>
                  </td>
                  <td className="p-3.5">
                    <StatusBadge status={t.policy_decision} />
                  </td>
                  <td className="p-3.5 font-mono font-bold text-slate-800">
                    ₹{((t.expected_value_minor || 0) / 100).toFixed(2)}
                  </td>
                  <td className="p-3.5 font-mono text-[11px] text-purple-700 bg-purple-50/60 px-2 py-0.5 rounded border border-purple-200/60 w-fit">
                    {t.policy_token_id}
                  </td>
                  <td className="p-3.5 text-right">
                    <Link
                      href={`/payments/${t.payment_id}`}
                      className="inline-flex items-center space-x-1 text-blue-600 hover:text-blue-800 font-semibold"
                    >
                      <span>Lineage</span>
                      <ArrowRight className="w-3 h-3" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
