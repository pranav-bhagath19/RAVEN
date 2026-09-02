"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchApi } from "../../lib/api";
import { StatusBadge } from "../../components/StatusBadge";
import { TableSkeleton } from "../../components/SkeletonLoader";
import { ExternalLink, Filter, Mail, MessageSquare, PhoneCall, RefreshCw, Send, Zap } from "lucide-react";

interface RecoveryItem {
  recovery_id: string;
  payment_id: string;
  customer_id: string;
  channel: string;
  action_type: string;
  status: string;
  amount_minor: number;
  created_at: string;
}

export default function RecoveriesPage() {
  const [recoveries, setRecoveries] = useState<RecoveryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApi<any>("/operations/tool-executions")
      .then((res) => {
        const list = Array.isArray(res) ? res : res?.items || [];
        setRecoveries(
          list.map((item: any) => ({
            recovery_id: item.execution_id || item.action_id || `rec_${item.payment_id}`,
            payment_id: item.payment_id,
            customer_id: item.parameters?.customer_id || "cust_active",
            channel: item.tool_name?.includes("WHATSAPP") ? "WHATSAPP" : item.tool_name?.includes("EMAIL") ? "EMAIL" : "RAZORPAY_API",
            action_type: item.tool_name || "SMART_RETRY",
            status: item.status || "EXECUTED",
            amount_minor: item.parameters?.amount_minor || 0,
            created_at: item.executed_at || new Date().toISOString(),
          }))
        );
        setLoading(false);
      })
      .catch(() => {
        setRecoveries([]);
        setLoading(false);
      });
  }, []);

  const getChannelIcon = (channel: string) => {
    if (channel === "WHATSAPP") return <MessageSquare className="w-3.5 h-3.5 text-emerald-600 mr-1" />;
    if (channel === "EMAIL") return <Mail className="w-3.5 h-3.5 text-blue-600 mr-1" />;
    return <PhoneCall className="w-3.5 h-3.5 text-indigo-600 mr-1" />;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center">
            <Zap className="w-5 h-5 text-amber-500 mr-2" /> Active Recovery Executions
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Multichannel recovery dispatches (Twilio WhatsApp, SendGrid Email, Razorpay Checkout Links)
          </p>
        </div>
      </div>

      {loading ? (
        <TableSkeleton rows={5} cols={6} />
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[11px]">
                <th className="p-3.5">Recovery ID</th>
                <th className="p-3.5">Payment ID</th>
                <th className="p-3.5">Channel</th>
                <th className="p-3.5">Action Executed</th>
                <th className="p-3.5">Amount</th>
                <th className="p-3.5">Verification Status</th>
                <th className="p-3.5 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {recoveries.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-xs text-slate-400 font-medium">
                    No active recovery executions recorded yet.
                  </td>
                </tr>
              ) : (
                recoveries.map((r) => (
                  <tr key={r.recovery_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="p-3.5 font-mono font-bold text-slate-900">{r.recovery_id}</td>
                    <td className="p-3.5 font-mono text-blue-600 font-semibold">{r.payment_id}</td>
                    <td className="p-3.5">
                      <span className="inline-flex items-center font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                        {getChannelIcon(r.channel)}
                        {r.channel}
                      </span>
                    </td>
                    <td className="p-3.5 font-semibold text-slate-800">{r.action_type}</td>
                    <td className="p-3.5 font-mono font-bold text-slate-900">
                      ₹{(r.amount_minor / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </td>
                    <td className="p-3.5">
                      <StatusBadge status={r.status} />
                    </td>
                    <td className="p-3.5 text-right">
                      <Link
                        href={`/payments/${r.payment_id}`}
                        className="inline-flex items-center space-x-1 text-blue-600 hover:text-blue-800 font-semibold"
                      >
                        <span>Trace</span>
                        <ExternalLink className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
